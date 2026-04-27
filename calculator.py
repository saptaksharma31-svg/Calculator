import ast
import operator as op
import tkinter as tk
from tkinter import ttk

ALLOWED_BINOPS = {
	ast.Add: op.add,
	ast.Sub: op.sub,
	ast.Mult: op.mul,
	ast.Div: op.truediv,
	ast.Pow: op.pow,
	ast.Mod: op.mod,
}


def safe_eval(expr: str):
	"""Evaluate arithmetic expression safely using ast."""
	expr = expr.replace('×', '*').replace('÷', '/')

	def _eval(node):
		if isinstance(node, ast.Expression):
			return _eval(node.body)
		if isinstance(node, ast.Num):
			return node.n
		if isinstance(node, ast.Constant):
			if isinstance(node.value, (int, float)):
				return node.value
			raise ValueError('Unsupported constant')
		if isinstance(node, ast.BinOp):
			left = _eval(node.left)
			right = _eval(node.right)
			op_type = type(node.op)
			if op_type in ALLOWED_BINOPS:
				return ALLOWED_BINOPS[op_type](left, right)
			raise ValueError('Unsupported binary operator')
		if isinstance(node, ast.UnaryOp):
			operand = _eval(node.operand)
			if isinstance(node.op, ast.UAdd):
				return +operand
			if isinstance(node.op, ast.USub):
				return -operand
			raise ValueError('Unsupported unary op')
		if isinstance(node, ast.Call):
			raise ValueError('Function calls not allowed')
		raise ValueError(f'Unsupported expression: {node!r}')

	node = ast.parse(expr, mode='eval')
	return _eval(node)


class Calculator(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title('Calculator')
		self.resizable(False, False)
		self.configure(padx=8, pady=8)

		self._expr_var = tk.StringVar()
		self._history = []

		self._create_widgets()
		self._bind_keys()

	def _create_widgets(self):
		# Color theme
		BG = '#1f2937'         # window background
		DISP_BG = '#0b1020'    # display background
		DISP_FG = '#e6eef8'
		DIGIT_BG = '#2b3440'
		DIGIT_FG = '#ffffff'
		OP_BG = '#ff9f0a'
		OP_FG = '#ffffff'
		FUNC_BG = '#5b6470'
		FUNC_FG = '#ffffff'
		EQUAL_BG = '#0a84ff'
		EQUAL_FG = '#ffffff'

		self.configure(bg=BG)
		top = tk.Frame(self, bg=BG)
		top.grid(row=0, column=0, sticky='nsew')

		display = tk.Entry(top, textvariable=self._expr_var, font=('Segoe UI', 22), justify='right',
						   bg=DISP_BG, fg=DISP_FG, bd=0, relief='flat', insertbackground=DISP_FG)
		display.grid(row=0, column=0, columnspan=4, sticky='ew', pady=(0, 8), ipady=12)
		display.focus_set()

		btns = [
			('C', 1, 0), ('⌫', 1, 1), ('(', 1, 2), (')', 1, 3),
			('7', 2, 0), ('8', 2, 1), ('9', 2, 2), ('÷', 2, 3),
			('4', 3, 0), ('5', 3, 1), ('6', 3, 2), ('×', 3, 3),
			('1', 4, 0), ('2', 4, 1), ('3', 4, 2), ('-', 4, 3),
			('0', 5, 0), ('.', 5, 1), ('%', 5, 2), ('+', 5, 3),
			('=', 6, 0, 4),
		]

		def make_button(text, r, c, colspan=1):
			if text == '=':
				bg, fg = EQUAL_BG, EQUAL_FG
			elif text in '0123456789.':
				bg, fg = DIGIT_BG, DIGIT_FG
			elif text in ('+', '-', '×', '÷', '%'):
				bg, fg = OP_BG, OP_FG
			else:
				bg, fg = FUNC_BG, FUNC_FG

			btn = tk.Button(top, text=text, bg=bg, fg=fg, activebackground=bg, activeforeground=fg,
							font=('Segoe UI', 13), bd=0, relief='raised', command=lambda t=text: self._on_button(t))
			btn.grid(row=r, column=c, columnspan=colspan, sticky='nsew', padx=6, pady=6)
			btn.bind('<Enter>', lambda e, b=btn: b.config(relief='groove'))
			btn.bind('<Leave>', lambda e, b=btn: b.config(relief='raised'))
			return btn

		for spec in btns:
			text = spec[0]
			r = spec[1]
			c = spec[2]
			colspan = spec[3] if len(spec) > 3 else 1
			make_button(text, r, c, colspan)

		for i in range(4):
			top.columnconfigure(i, weight=1)

		# History pane (styled)
		side = tk.Frame(self, bg=BG)
		side.grid(row=0, column=1, sticky='ns', padx=(8, 0))
		lbl = tk.Label(side, text='History', font=('Segoe UI', 10, 'bold'), bg=BG, fg=DISP_FG)
		lbl.pack(anchor='w')
		self._hist_box = tk.Listbox(side, height=12, width=28, bg=DIGIT_BG, fg=DIGIT_FG, bd=0, highlightthickness=0)
		self._hist_box.pack(side='left', fill='y', pady=(4,0))
		sb = tk.Scrollbar(side, orient='vertical', command=self._hist_box.yview)
		sb.pack(side='left', fill='y')
		self._hist_box.config(yscrollcommand=sb.set)
		self._hist_box.bind('<<ListboxSelect>>', self._on_history_select)

	def _on_button(self, label: str):
		if label == 'C':
			self._expr_var.set('')
			return
		if label == '⌫':
			self._expr_var.set(self._expr_var.get()[:-1])
			return
		if label == '%':
			# convert x% into (x/100)
			cur = self._expr_var.get()
			if cur:
				try:
					val = safe_eval(cur)
					self._expr_var.set(str(val / 100))
				except Exception:
					self._expr_var.set('Error')
			return
		if label == '=':
			self._calculate()
			return
		# append other button text
		self._expr_var.set(self._expr_var.get() + label)

	def _calculate(self):
		expr = self._expr_var.get().strip()
		if not expr:
			return
		try:
			result = safe_eval(expr)
			# format result nicely
			if isinstance(result, float) and result.is_integer():
				result = int(result)
			out = str(result)
			self._history.insert(0, f'{expr} = {out}')
			self._refresh_history()
			self._expr_var.set(out)
		except Exception:
			self._expr_var.set('Error')

	def _refresh_history(self):
		self._hist_box.delete(0, tk.END)
		for item in self._history:
			self._hist_box.insert(tk.END, item)

	def _on_history_select(self, event):
		sel = event.widget.curselection()
		if not sel:
			return
		idx = sel[0]
		item = self._history[idx]
		# split on = to get result or expression
		if '=' in item:
			expr, res = item.split('=', 1)
			expr = expr.strip()
			self._expr_var.set(expr)

	def _bind_keys(self):
		self.bind('<Return>', lambda e: self._calculate())
		self.bind('<KP_Enter>', lambda e: self._calculate())
		self.bind('<BackSpace>', lambda e: self._expr_var.set(self._expr_var.get()[:-1]))
		self.bind('<Escape>', lambda e: self._expr_var.set(''))
		for k in '0123456789.+-*/()':
			self.bind(k, lambda e, ch=k: self._expr_var.set(self._expr_var.get() + ch))


if __name__ == '__main__':
	app = Calculator()
	app.mainloop()

