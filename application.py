"""
Elastic Beanstalk entry point.
This file is required for Elastic Beanstalk deployment.
It imports the Flask app from app.py
"""

from app import app

# Elastic Beanstalk looks for 'application' variable
application = app

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=5000, debug=False)

