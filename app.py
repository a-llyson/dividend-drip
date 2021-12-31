from flask import Flask, render_template, request
from calculations import find_best_dividend
app = Flask(__name__)



@app.route("/", methods=['POST', 'GET'])
def find_stocks():
   if request.method == 'POST':
      budget = request.form['money']
      if budget == "":
          return render_template('home.html')
      list_of_combinations = find_best_dividend(float(budget))
      return render_template('results.html', stock_combos=list_of_combinations, budget=budget)
   else:
      return render_template('home.html')