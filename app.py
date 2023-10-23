from flask import Flask, request, jsonify,render_template
from graphene import  String, Float, Field, Schema
from ariadne import QueryType, ObjectType,graphql_sync, MutationType, make_executable_schema, load_schema_from_path
from graphene import  String, Schema
from graphql_server.flask import GraphQLView
from ariadne.constants import CONTENT_TYPE_TEXT_HTML
from flask_socketio import SocketIO
import random
from time import sleep
import datetime
import time

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
    day_max:Float!
    day_min:Float!
    stock_history: [StockHistory!]!
}

type StockHistory {
    price_at_time:String!
    name: String!
    ticker: String!
    currentPrice: Float!
    day_max:Float!
    day_min:Float!
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
        'amz': {'name': 'Amazon', 'ticker': 'amz','currentPrice':'100', 'stock_history':[], 'day_max':'0', 'day_min':'100'},
        'mta': {'name': 'Meta', 'ticker': 'mta','currentPrice':'50', 'stock_history':[], 'day_max':'0', 'day_min':'100'},
    }
# users = {
#         '1': {'name': 'Alice', 'email': 'alice@example.com'},
#         '2': {'name': 'Bob', 'email': 'bob@example.com'}
#     }

@app.route('/stocks', methods=['POST','GET'])
def handle_stocks():
    print('handle')
    if request.method == 'POST':
        print('in post')
        new_stock = request.get_json()
        print(new_stock)
        required_keys = ['name',  'ticker','currentPrice']

        if all(key in new_stock for key in required_keys):
            new_stock['stock_history'] = []
            new_stock['day_max'] = new_stock['currentPrice']
            new_stock['day_min'] = new_stock['currentPrice']

            stocks[new_stock['ticker']] = new_stock
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
            r_num = str(random.randint(1, 100))
            stock['currentPrice']  = r_num
            if(int(r_num)<int(stock['day_min'])):
                stock['day_min'] = r_num
            if(int(r_num)>int(stock['day_max'])):
                stock['day_max'] = r_num
            
            stock_cpy = {
                'name':stock['name'],
                'ticker':stock['ticker'],
                'currentPrice':stock['currentPrice'],
                'day_max':stock['day_max'],
                'day_min':stock['day_min'],
                'price_at_time':str(time.time())
            }
            stock['stock_history'].append(stock_cpy)
        socketio.emit('stock_data', stocks)  

@app.route('/<ticker>')
def view_stock(ticker):
    return render_template('stock.html', ticker=ticker)

if __name__ == '__main__':
    socketio.run(app, debug=True)
