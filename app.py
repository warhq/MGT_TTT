from flask import Flask, render_template, request
import api_calls
import world_data

app = Flask(__name__)

_tables = world_data.load_tables()


@app.template_filter('credits')
def credits_filter(value):
    return f"Cr{value:,}"


@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    error = None
    sector    = request.form.get('sector',     'Spinward Marches')
    hex_code  = request.form.get('hex_code',   '1433')
    jump_range = request.form.get('jump_range', '3')

    if request.method == 'POST':
        try:
            jump = max(1, min(6, int(jump_range)))
        except ValueError:
            jump = 3

        worlds = api_calls.fetch_worlds(sector, hex_code, jump)
        if not worlds:
            error = "No worlds found. Check your inputs or internet connection."
        else:
            results = [world_data.process_world(w, hex_code, _tables) for w in worlds]

    return render_template('index.html',
                           results=results,
                           sector=sector,
                           hex_code=hex_code,
                           jump_range=jump_range,
                           error=error)


if __name__ == '__main__':
    app.run(debug=True)
