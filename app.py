from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3

import signal
import unittest
import time

import threading
import queue

import os


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

import boto3
from decimal import Decimal


aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

class TestKnightAttack(unittest.TestCase):


    def setUp(self):
        self.knight_attack = globals().get('knight_attack', None)

    def test_1(self):
        start_time = time.time()
        try:
            self.assertEqual(self.knight_attack(8, 1, 1, 2, 2), 2, "2 Moves are Required")
        finally:
            self.duration = time.time() - start_time
    def test_2(self):
        start_time = time.time()
        try:
            self.assertEqual(self.knight_attack(8, 1, 1, 2, 3), 1, "1 Moves are Required")
        finally:
            self.duration = time.time() - start_time
    def test_3(self):
        start_time = time.time()
        try:
            self.assertEqual(self.knight_attack(8, 0, 3, 4, 2), 3, "2 Moves are Required")
        finally:
            self.duration = time.time() - start_time
    def test_4(self):
        start_time = time.time()
        try:
            self.assertEqual(self.knight_attack(8, 0, 3, 5, 2), 4, "2 Moves are Required")
        finally:
            self.duration = time.time() - start_time
    def test_5(self):
        start_time = time.time()
        try:
            self.assertEqual(self.knight_attack(24, 4, 7, 19, 20), 10, "2 Moves are Required")
        finally:
            self.duration = time.time() - start_time
    def test_6(self):
        start_time = time.time()
        try:
            self.assertEqual(self.knight_attack(100, 21, 10, 0, 0), 11, "2 Moves are Required")
        finally:
            self.duration = time.time() - start_time
    def test_7(self):
        start_time = time.time()
        try:
            self.assertEqual(self.knight_attack(3, 0, 0, 1, 2), 1, "2 Moves are Required")
        finally:
            self.duration = time.time() - start_time
    def test_8(self):
        start_time = time.time()
        try:
            self.assertEqual(self.knight_attack(3, 0, 0, 1, 1), None, "2 Moves are Required")
        finally:
            self.duration = time.time() - start_time



def execute_user_code(code):

    local_vars = {}
    try:
        exec(code, globals(), local_vars)
        return {"success": True, "data": local_vars}
    except Exception as e:
        return {"success": False, "error": str(e)}
    return local_vars


def run_test(test_queue, test):
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test)
    test_queue.put(result)

def update_score(user_id, question, score):
    dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
    table = dynamodb.Table('take-home-final')
    new_score = score * 100
    new_score = Decimal(f"{new_score:.2f}")

    response = table.get_item(
        Key={
            'userID': user_id,
            'questionName': question
        }
    )

    item = response.get('Item')
    if item:
        current_score = item['Score']
        if new_score > current_score:
            print("Updating score as the new score is higher...")
            table.update_item(
                Key={
                    'userID': user_id,
                    'questionName': question
                },
                UpdateExpression="set Score = :s",
                ExpressionAttributeValues={
                    ':s': new_score
                },
                ReturnValues="UPDATED_NEW"
            )
            print("Score updated.")
        else:
            print("Existing score is higher or equal; no update performed.")
    else:
        print("No existing score found, adding new score...")
        table.put_item(
            Item={
                'userID': user_id,
                'questionName': question,
                'Score': new_score
            }
        )
        print("New score added.")

@app.route('/runCode', methods=['POST', 'GET'])
def runCode():

    code = request.json['code']
    user = request.json['user']

    print(user)
    print(code)
    user_funcs = execute_user_code(code)
    print(user_funcs)
    if user_funcs["success"]:
        globals().update(user_funcs["data"])
        loader = unittest.TestLoader()
        suite = unittest.TestSuite(loader.loadTestsFromTestCase(TestKnightAttack))

        results = {'passed': True, 'results': []}
        correct = 0
        for test in suite:
            test_queue = queue.Queue()
            test_thread = threading.Thread(target=run_test, args=(test_queue, test))
            test_thread.start()

            test_thread.join(timeout=2)


            if test_thread.is_alive():
                test_thread.join(timeout=0)
                results = {'passed': False, 'results': ["One or more tests timed out. Re-check your code"]}
                return jsonify(results)

            result = test_queue.get()
            if result.wasSuccessful():
                result_message = {
                    'test': str(test),
                    'passed': True,
                    'duration': getattr(test, 'duration', 'Duration not set')
                }

                correct += 1

                results["results"].append(result_message)
            else:
                result_message = {
                    'test': str(test),
                    'passed': False,
                    'duration': getattr(test, 'duration', 'Duration not set')
                }


                results["results"].append(result_message)

    else:
        results = {'passed': False, 'results': ["Code did not compile"]}
        return jsonify(results)

    print(results)

    score = correct / len(results['results'])
    update_score(user, "KnightAttack", score)
    return jsonify(results)






if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)