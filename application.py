import os
from flask import url_for
import models
import routes

application = app = routes.app

if __name__ == '__main__':
   
   
    application.run(debug = True,threaded=True)
