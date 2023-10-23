from flask import Flask, request, jsonify,render_template
from graphene import  String, Float, Field, Schema
from ariadne import QueryType, ObjectType,graphql_sync, MutationType, make_executable_schema, load_schema_from_path
from graphene import  String, Schema
from graphql_server.flask import GraphQLView
from ariadne.constants import CONTENT_TYPE_TEXT_HTML
from flask_socketio import SocketIO
import random
from time import sleep

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

type_defs = """
type Query {
    stock(ticker: String!): Stock
    stocks: [Stock!]!
}

type Stock {
    name: String!
    ticker: String!
    currentPrice: Float!
}
"""


query = QueryType()
stock = ObjectType("Stock")

@query.field("stock")
def resolve_stock(*_, ticker):
    return stocks.get(ticker, {})


@query.field("stocks")
def resolve_stocks(*_):
    return stocks


schema = make_executable_schema(type_defs, query,stock)

stocks= {
        'amz': {'name': 'Amazon', 'ticker': 'amz','currentPrice':'100'},
        'mta': {'name': 'Meta', 'ticker': 'mta','currentPrice':'50'},
    }
users = {
        '1': {'name': 'Alice', 'email': 'alice@example.com'},
        '2': {'name': 'Bob', 'email': 'bob@example.com'}
    }

@app.route('/stocks', methods=['POST','GET'])
def handle_stocks():
    print('handle')
    if request.method == 'POST':
        print('in post')
        new_stock = request.get_json()
        print(new_stock)
        required_keys = ['name',  'ticker','currentPrice']

        if all(key in new_stock for key in required_keys):
            stocks[str(len(stocks.keys()) + 1)] = new_stock
            print(stocks)
            return jsonify({"success":True})
        else:
            return jsonify({"success":False, "msg": "Please pass all the data"})
    else:
        return jsonify(stocks)


@app.route('/stocks/<id>')
def rest_get_stocks(id):
    
    stock_info = stocks.get(id, {})
    print(stock_info)
    return jsonify(stock_info)

class Stock(ObjectType):
    name = String(description="Name of the stock.")
    ticker = String(description="Ticker symbol of the stock.")
    current_price = Float(description="Current price of the stock.")


class Query(ObjectType):
    stock = Field(Stock, ticker=String(required=True, description="Ticker symbol of the stock to query."))

    def resolve_stock(self, info, ticker):
        return stocks.get(ticker)
    
@socketio.on('connect')
def handle_connect():
    socketio.start_background_task(update_stock_prices)
    print('client connected')

# app.add_url_rule(
#     '/stocks-graphql',
#     view_func=GraphQLView.as_view(
#         'graphql',
#         schema=schema,
#         graphiql=True  # Enable GraphiQL interface
#     )
# )
app.add_url_rule("/graphql", view_func=GraphQLView.as_view("graphql", schema=schema, graphiql=True))

@app.route('/stocks-graphql', methods=['GET', 'POST'])
def graphql_server():
    if request.method == 'GET':
        return CONTENT_TYPE_TEXT_HTML, 200

    data = request.get_json()
    success, result = graphql_sync(
        schema,
        data,
        context_value=request,
        debug=app.debug
    )

    status_code = 200 if success else 400
    return jsonify(result), status_code

@socketio.on('get_stock')
def handle_get_stock(ticker):
    print('asdasdasdasd2')
    stock = stocks.get(ticker)
    if stock:
        socketio.emit('stock_data', stock)

@app.route('/')
def index():
    return render_template('index.html')

def update_stock_prices():
    print('asd')
    while True:
        socketio.sleep(10)
        print('updating...')
        for stock in stocks.values():
            stock['currentPrice'] = str(random.randint(1, 100))  
        socketio.emit('stock_data', stocks)  

@app.route('/<ticker>')
def view_stock(ticker):
    return render_template('stock.html', ticker=ticker)

if __name__ == '__main__':
    socketio.run(app, debug=True)
