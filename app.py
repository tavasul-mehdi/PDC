from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "supersecretkey"

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Expense model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=db.func.current_timestamp())

# Initialize database
if not os.path.exists('expenses.db'):
    with app.app_context():
        db.create_all()

# Home route
@app.route('/')
def home():
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    categories = db.session.query(Expense.category, db.func.sum(Expense.amount)).group_by(Expense.category).all()
    return render_template('index.html', expenses=expenses, categories=categories)

# Add expense
@app.route('/add', methods=['POST'])
def add_expense():
    title = request.form.get('title')
    amount = request.form.get('amount')
    category = request.form.get('category')

    if not title or not amount or not category:
        flash('All fields are required!', 'error')
        return redirect(url_for('home'))

    try:
        new_expense = Expense(title=title, amount=float(amount), category=category)
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
    except ValueError:
        flash('Invalid amount. Please enter a number.', 'error')
    return redirect(url_for('home'))

# Delete expense
@app.route('/delete/<int:id>')
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('home'))

# Edit expense
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    if request.method == 'POST':
        expense.title = request.form.get('title')
        expense.amount = request.form.get('amount')
        expense.category = request.form.get('category')
        if not expense.title or not expense.amount or not expense.category:
            flash('All fields are required!', 'error')
            return redirect(url_for('edit_expense', id=id))
        try:
            expense.amount = float(expense.amount)
            db.session.commit()
            flash('Expense updated successfully!', 'success')
        except ValueError:
            flash('Invalid amount. Please enter a number.', 'error')
            return redirect(url_for('edit_expense', id=id))
        return redirect(url_for('home'))
    return render_template('edit.html', expense=expense)

# API route for chart data
@app.route('/chart-data')
def chart_data():
    categories = db.session.query(Expense.category, db.func.sum(Expense.amount)).group_by(Expense.category).all()
    return jsonify({category: amount for category, amount in categories})

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
