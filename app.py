from flask import Flask

# Create the web app object
app = Flask(__name__)

# This is like our home page: "/"
@app.route("/")
def home():
    return "Schwab bot is alive 🧠📈"

# This only runs when we start it directly (not on Render)
if __name__ == "__main__":
    # 0.0.0.0 = listen to all connections
    # port 5000 = common default port
    app.run(host="0.0.0.0", port=5000)
