# -*- coding: utf-8 -*-
"""
Android 快速版（Kivy + Pydroid 3）
- 在手机上用 Pydroid 3 安装依赖后直接运行本脚本
- 复用 盈利计算.py 的计算逻辑（PositionPlan/LumpExit/GridExit/compute_schedule_pnl/pv）
- 界面支持逐行添加固定价/网格（无需手动逗号）

Pydroid 3 中准备：
 1) 打开 Pydroid 3 → Pip → 安装 kivy pandas
 2) 将本项目两份文件放入可访问目录：盈利计算.py, Android_快速版_Kivy.py
 3) 在 Pydroid 3 打开 Android_快速版_Kivy.py，运行
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.core.window import Window
from calc_core_alias import PositionPlan, LumpExit, GridExit, compute_schedule_pnl_core, pv


def safe_int(s: str) -> int:
    return int(float(s))


def dict_group_min_max_sum(rows: List[Dict[str, Any]], key: Tuple[str, str]) -> List[Dict[str, Any]]:
    # 以 (grid_index, grid_label) 分组后汇总区间和总手数
    g: Dict[Tuple[Any, Any], Dict[str, Any]] = {}
    for r in rows:
        k = (r.get('grid_index'), r.get('grid_label')) if key else ('type', None)
        if k not in g:
            g[k] = {
                'min_price': r['price'],
                'max_price': r['price'],
                'total_qty': int(r['qty']),
                'grid_index': r.get('grid_index'),
                'grid_label': r.get('grid_label'),
            }
        else:
            g[k]['min_price'] = min(g[k]['min_price'], r['price'])
            g[k]['max_price'] = max(g[k]['max_price'], r['price'])
            g[k]['total_qty'] += int(r['qty'])
    out = []
    for (_idx, _lab), v in g.items():
        out.append(v)
    return out


def format_results_mobile(fills: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    out = []
    out.append("— 计算结果 —")
    for k in ["symbol", "side", "avg_entry", "point_value", "total_qty", "closed_qty", "remaining_qty", "mark_price", "grid_sort"]:
        out.append(f"{k:>18}: {summary[k]}")
    out.append(f"{'realized_pnl_usd':>18}: ${summary['realized_pnl_usd']:,.2f}")
    out.append(f"{'unrealized_pnl_usd':>18}: ${summary['unrealized_pnl_usd']:,.2f}")
    out.append(f"{'total_pnl_usd':>18}: ${summary['total_pnl_usd']:,.2f}")
    if summary.get('weighted_avg_exit') is not None:
        out.append(f"{'weighted_avg_exit':>18}: {summary['weighted_avg_exit']:.2f}")

    if not fills:
        out.append("\n无成交明细：目标价未触发任何固定价/网格位")
        return "\n".join(out)

    # 拆分固定价/网格
    lumps = [r for r in fills if r.get('type') == 'lump']
    grids = [r for r in fills if r.get('type') == 'grid']

    # 固定价逐条
    if lumps:
        out.append("\n— 固定价成交 —")
        out.append(f"{'序号':>4} {'价格':>10} {'手数':>6} {'盈亏点':>8} {'盈亏USD':>12}")
        for i, row in enumerate(lumps):
            out.append(f"{i+1:>4} {row['price']:>10.2f} {int(row['qty']):>6d} {row['pnl_pts']:>8.2f} {row['pnl_usd']:>12.2f}")

    # 网格按组汇总（区间+总手数）
    if grids:
        rows = [
            {
                'price': float(r['price']),
                'qty': int(r['qty']),
                'grid_index': r.get('grid_index'),
                'grid_label': r.get('grid_label'),
            }
            for r in grids
        ]
        aggs = dict_group_min_max_sum(rows, ('grid_index', 'grid_label'))
        out.append("\n— 网格执行汇总 —")
        out.append(f"{'组/标签':<10} {'区间':<23} {'总手数':>6}")
        for r in aggs:
            label_val = r.get('grid_label')
            idx_val = r.get('grid_index')
            if (label_val is None) and (idx_val is not None):
                label = f"G{idx_val}"
            elif label_val is None:
                label = ''
            else:
                label = str(label_val)
            interval = f"{r['min_price']:.2f} ~ {r['max_price']:.2f}"
            out.append(f"{label:<10} {interval:<23} {int(r['total_qty']):>6d}")

    return "\n".join(out)


class QuickRoot(BoxLayout):
    pass


class QuickCalcApp(App):
    def build(self):
        Window.size = (420, 780)
        root = BoxLayout(orientation='vertical')

        scroll = ScrollView(size_hint=(1, None), size=(Window.width, Window.height * 0.6))
        form = GridLayout(cols=2, size_hint_y=None, padding=8, spacing=6)
        form.bind(minimum_height=form.setter('height'))

        # 合约 / 方向 / 手数
        form.add_widget(Label(text='合约'))
        self.sp_symbol = Spinner(text='NQ', values=('NQ', 'MNQ'), size_hint_x=1)
        form.add_widget(self.sp_symbol)

        form.add_widget(Label(text='方向'))
        self.sp_side = Spinner(text='long', values=('long', 'short'))
        form.add_widget(self.sp_side)

        form.add_widget(Label(text='手数'))
        self.ti_qty = TextInput(text='1', multiline=False, input_filter='int')
        form.add_widget(self.ti_qty)

        # 均价推算方式
        form.add_widget(Label(text='用 当前价+盈亏 推算均价'))
        cb_box = BoxLayout(orientation='horizontal')
        self.cb_use_formula = CheckBox(active=True)
        cb_box.add_widget(self.cb_use_formula)
        form.add_widget(cb_box)

        form.add_widget(Label(text='当前价格'))
        self.ti_cur = TextInput(text='0', multiline=False, input_filter='float')
        form.add_widget(self.ti_cur)

        form.add_widget(Label(text='当前盈亏USD'))
        self.ti_pnl = TextInput(text='0', multiline=False, input_filter='float')
        form.add_widget(self.ti_pnl)

        form.add_widget(Label(text='或 手动均价'))
        self.ti_avg = TextInput(text='0', multiline=False, input_filter='float')
        form.add_widget(self.ti_avg)

        form.add_widget(Label(text='目标/估值价格'))
        self.ti_mark = TextInput(text='0', multiline=False, input_filter='float')
        form.add_widget(self.ti_mark)

        form.add_widget(Label(text='网格排序'))
        self.sp_sort = Spinner(text='price', values=('price', 'group_order'))
        form.add_widget(self.sp_sort)

        # 固定价行集
        form.add_widget(Label(text='固定价行'))
        self.lumps_box = BoxLayout(orientation='vertical', size_hint_y=None)
        self.lumps_box.bind(minimum_height=self.lumps_box.setter('height'))
        self.add_lump_row()
        form.add_widget(self.lumps_box)

        btn_lump_row = BoxLayout()
        btn_lump = Button(text='添加固定价')
        btn_lump.bind(on_press=lambda *_: self.add_lump_row())
        btn_lump_row.add_widget(Widget())
        btn_lump_row.add_widget(btn_lump)
        form.add_widget(Label(text=''))
        form.add_widget(btn_lump_row)

        # 网格行集
        form.add_widget(Label(text='网格行'))
        self.grids_box = BoxLayout(orientation='vertical', size_hint_y=None)
        self.grids_box.bind(minimum_height=self.grids_box.setter('height'))
        self.add_grid_row()
        form.add_widget(self.grids_box)

        btn_grid_row = BoxLayout()
        btn_grid = Button(text='添加网格')
        btn_grid.bind(on_press=lambda *_: self.add_grid_row())
        btn_grid_row.add_widget(Widget())
        btn_grid_row.add_widget(btn_grid)
        form.add_widget(Label(text=''))
        form.add_widget(btn_grid_row)

        scroll.add_widget(form)
        root.add_widget(scroll)

        # 操作按钮 + 仅改目标价
        ops = BoxLayout(size_hint_y=None, height=48, padding=8, spacing=8)
        self.ti_mark_new = TextInput(hint_text='新目标/估值价格', multiline=False, input_filter='float')
        btn_calc = Button(text='计算')
        btn_recalc = Button(text='仅改目标价重算')
        btn_calc.bind(on_press=lambda *_: self.on_calc(None))
        btn_recalc.bind(on_press=lambda *_: self.on_calc(self.ti_mark_new.text.strip() or None))
        ops.add_widget(btn_calc)
        ops.add_widget(self.ti_mark_new)
        ops.add_widget(btn_recalc)
        root.add_widget(ops)

        # 输出
        self.out = TextInput(readonly=True, size_hint=(1, 1))
        root.add_widget(self.out)

        return root

    def add_lump_row(self):
        row = BoxLayout(size_hint_y=None, height=36, spacing=4)
        ti_price = TextInput(hint_text='价格', multiline=False, input_filter='float')
        ti_qty = TextInput(hint_text='手数', multiline=False, input_filter='int')
        btn_del = Button(text='删', size_hint_x=None, width=40)
        row.add_widget(ti_price)
        row.add_widget(ti_qty)
        row.add_widget(btn_del)
        self.lumps_box.add_widget(row)
        btn_del.bind(on_press=lambda *_: self.lumps_box.remove_widget(row))

    def add_grid_row(self):
        row = BoxLayout(size_hint_y=None, height=36, spacing=4)
        ti_label = TextInput(hint_text='标签', multiline=False)
        ti_start = TextInput(hint_text='起始', multiline=False, input_filter='float')
        ti_end = TextInput(hint_text='终止', multiline=False, input_filter='float')
        ti_step = TextInput(hint_text='步长', multiline=False, input_filter='float')
        ti_qpl = TextInput(hint_text='每级手数', multiline=False, input_filter='int')
        btn_del = Button(text='删', size_hint_x=None, width=40)
        for w in (ti_label, ti_start, ti_end, ti_step, ti_qpl, btn_del):
            row.add_widget(w)
        self.grids_box.add_widget(row)
        btn_del.bind(on_press=lambda *_: self.grids_box.remove_widget(row))

    def read_lumps(self) -> List[LumpExit]:
        res: List[LumpExit] = []
        for row in list(self.lumps_box.children)[::-1]:  # children 逆序
            if not isinstance(row, BoxLayout) or len(row.children) < 3:
                continue
            # children 顺序为 [btn_del, ti_qty, ti_price]
            ti_qty = row.children[1]
            ti_price = row.children[2]
            s_price = ti_price.text.strip()
            s_qty = ti_qty.text.strip()
            if not s_price and not s_qty:
                continue
            if not s_price or not s_qty:
                raise ValueError('固定价行不完整：请填写价格与手数')
            res.append(LumpExit(price=float(s_price), qty=safe_int(s_qty)))
        return res

    def read_grids(self) -> List[GridExit]:
        res: List[GridExit] = []
        for row in list(self.grids_box.children)[::-1]:
            if not isinstance(row, BoxLayout) or len(row.children) < 6:
                continue
            # children 顺序：[btn_del, ti_qpl, ti_step, ti_end, ti_start, ti_label]
            ti_qpl = row.children[4-3]  # 实际按索引获取更安全，下面明确取
            ti_label = row.children[5]
            ti_start = row.children[4]
            ti_end = row.children[3]
            ti_step = row.children[2]
            ti_qpl = row.children[1]
            s_label = ti_label.text.strip()
            s_start = ti_start.text.strip()
            s_end = ti_end.text.strip()
            s_step = ti_step.text.strip()
            s_qpl = ti_qpl.text.strip()
            if not s_label and not s_start and not s_end and not s_step and not s_qpl:
                continue
            if not (s_label and s_start and s_end and s_step and s_qpl):
                raise ValueError('网格行不完整：请填写标签、起始、终止、步长、每级手数')
            res.append(GridExit(start=float(s_start), end=float(s_end), step=float(s_step), qty_per_level=safe_int(s_qpl), label=s_label))
        return res

    def on_calc(self, mark_override: Optional[str]):
        try:
            symbol = self.sp_symbol.text.strip()
            side = self.sp_side.text.strip()
            qty = safe_int(self.ti_qty.text.strip() or '0')
            if qty <= 0:
                raise ValueError('手数需大于 0')

            pv_usd = pv(symbol)
            use_formula = self.cb_use_formula.active

            if use_formula:
                cur = float(self.ti_cur.text.strip() or '0')
                pnl_usd = float(self.ti_pnl.text.strip() or '0')
                avg_entry = cur - pnl_usd / (pv_usd * qty) if side == 'long' else cur + pnl_usd / (pv_usd * qty)
            else:
                avg_entry = float(self.ti_avg.text.strip() or '0')

            if mark_override is not None:
                mark = float(mark_override)
            else:
                mark_s = self.ti_mark.text.strip()
                mark = float(mark_s) if mark_s else (float(self.ti_cur.text.strip() or '0') if use_formula else avg_entry)

            lumps = self.read_lumps()
            grids = self.read_grids()

            plan = PositionPlan(
                symbol=symbol, side=side, avg_entry=avg_entry, total_qty=qty,
                lumps=lumps, grids=grids, mark_price=mark, grid_sort=self.sp_sort.text
            )
            fills, summary = compute_schedule_pnl_core(plan)
            text = format_results_mobile(fills, summary)
            self.out.text = text
        except Exception as e:
            self.out.text = f"错误：{e}"


if __name__ == '__main__':
    QuickCalcApp().run()
