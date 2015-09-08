from flask import Flask, render_template, request, jsonify, redirect, url_for
from wtforms import StringField, IntegerField, ValidationError, widgets, SelectMultipleField, BooleanField


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def process_checkboxes():
    return render_template('index.html')

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


# def graph_json():

if __name__ == '__main__':
    app.run(debug=True)
