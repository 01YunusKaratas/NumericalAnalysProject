from flask import Flask, request, jsonify, render_template
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
import numpy as np
import sympy as sp
import ast
from threading import Thread
import requests
from queue import Queue
import queue  # Ekledik

app = Flask(__name__)
data_queue = Queue()  # Ekledik

def fixed_point_iteration(f, x_0, tol, max_iter):
    x_values = [x_0]
    iterations = 0

    x = sp.symbols('x')
    expr = sp.sympify(f)
    g = x - expr
    g_func = sp.lambdify(x, g, 'numpy')

    while iterations < max_iter:
        x_next = g_func(x_values[-1])
        x_values.append(x_next)

        try:
            if abs(expr.subs(x, x_next)) < tol or abs(x_values[-1] - x_values[-2]) < tol:
                break
        except Exception as e:
            print(f"Hata: {e}")
            break

        iterations += 1

    return x_values, iterations

def f(x):
    return x**2 - 2

def plot_iteration_process(ax, function, x_values):
    x_values = np.array(x_values)
    x = sp.symbols('x')
    expr = sp.sympify(function)
    y_values = np.vectorize(sp.lambdify(x, expr, 'numpy'))(x_values)

    ax.clear()
    ax.plot(x_values, y_values, label="f(x)")
    ax.scatter(x_values, y_values, color='red', label='Iterasyon Noktaları')
    ax.axhline(0, color='black', linewidth=0.8, linestyle='--', label="y=0")
    ax.axvline(x=x_values[-1], color='green', linestyle='--', label="Kök Yaklaşımı")

    ax.set_xlabel('x')
    ax.set_ylabel('f(x)')
    ax.set_title('Sabit Nokta İterasyonu Grafiği')
    ax.legend()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    function = data['function']
    initial_guess = float(data['initial_guess'])
    tolerance = float(data['tolerance'])
    max_iterations = int(data['max_iterations'])

    x_values, iterations = fixed_point_iteration(function, initial_guess, tolerance, max_iterations)

    result = {
        'root_approximation': x_values[-1],
        'iterations': iterations,
        'x_values': x_values  # x_values'ı ekleyin
    }

    data_queue.put(result)

    # JSON yanıtı döndür
    return jsonify(result)




class GUI(tk.Tk):
    def __init__(self, data_queue):
        tk.Tk.__init__(self)
        self.title("FIXED POINT ITERATION")
        self.configure(bg='orange')

        self.label_function = ttk.Label(self, text="Function ('x' variable):", background='grey', foreground='white')
        self.entry_function = ttk.Entry(self, width=30)

        self.label_initial_guess = ttk.Label(self, text="Starting Estimate:", background='grey', foreground='white')
        self.entry_initial_guess = ttk.Entry(self)

        self.label_tolerance = ttk.Label(self, text="Tolerance:", background='grey', foreground='white')
        self.entry_tolerance = ttk.Entry(self)

        self.label_max_iterations = ttk.Label(self, text="Maximum Number of Iterations:", background='grey', foreground='white')
        self.entry_max_iterations = ttk.Entry(self)

        style = ttk.Style()
        style.configure("TButton", background='red', foreground='white')
        self.button_run_iteration = ttk.Button(self, text="Calculate", command=self.run_iteration, style="TButton")

        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1, padx=10, pady=10)
        self.canvas_widget.configure(bg='grey')

        self.label_result = ttk.Label(self, text="Result: ", background='grey', foreground='white')

        self.label_function.pack()
        self.entry_function.pack()
        self.label_initial_guess.pack()
        self.entry_initial_guess.pack()
        self.label_tolerance.pack()
        self.entry_tolerance.pack()
        self.label_max_iterations.pack()
        self.entry_max_iterations.pack()
        self.button_run_iteration.pack(pady=10)
        self.label_result.pack()
        self.data_queue = data_queue
        self.after(100, self.check_data_queue)

    def check_data_queue(self):
        try:
            while True:
                data = self.data_queue.get_nowait()
                if 'function' in data and 'x_values' in data:
                    self.update_plot(data['function'], data['x_values'])
        except queue.Empty:
            pass
        self.after(100, self.check_data_queue)  # Düzeltildi

    def update_plot(self, function, x_values):
        plot_iteration_process(self.ax, function, x_values)
        self.canvas.draw()

    def run_iteration(self):
        function = self.entry_function.get()
        initial_guess = float(self.entry_initial_guess.get())
        tolerance_str = self.entry_tolerance.get()
        tolerance = float(self.evaluate_expression(tolerance_str))
        max_iterations = int(self.entry_max_iterations.get())

        data = {
            'function': function,
            'initial_guess': initial_guess,
            'tolerance': tolerance,
            'max_iterations': max_iterations
        }

        # Flask uygulamasına isteği gönder
        response = requests.post('http://127.0.0.1:5000/calculate', json=data)

        # Elde edilen sonuçları işle ve GUI'de görüntüle
        result = response.json()
        result_label_text = f"Result: Root Approximation: {result['root_approximation']}, Iterations: {result['iterations']}"
        self.label_result.config(text=result_label_text)

        x_values = response.json()['x_values']
        self.data_queue.put({'function': data['function'], 'x_values': x_values})

    def evaluate_expression(self, expression):
        try:
            ast_tree = ast.parse(expression, mode='eval')
            eval_result = eval(compile(ast_tree, filename="<string>", mode="eval"))
            return eval_result
        except Exception as e:
            print(f"Hata: {e}")
            return None
if __name__ == '__main__':
    def run_flask():
        app.run()

    thread_flask = Thread(target=run_flask)
    thread_flask.start()

    gui = GUI(data_queue)
    gui.mainloop()
    app.geometry("400x300")
