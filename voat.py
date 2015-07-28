'''
    RealFakeVout-Api

    API for the RealFakeVout App! Much glorious, very wow.
'''

from flask import Flask, jsonify, make_response, request, current_app
from requests import get, post, delete, put
from datetime import timedelta
from functools import update_wrapper
from json import loads, dumps
from os import environ

app = Flask(__name__)
headers = {
    'Content-Type': 'application/json',
    'Voat-ApiKey': environ['VOAT_KEY']
}

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    '''
     method for allowing cross-domain connections
    '''
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        '''
         utils method for obtaining methods
        '''
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(func):
        '''
         decorator for cross-domain sanitation
        '''
        def wrapped_function(*args, **kwargs):
            '''
             representation of specified route
            '''
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(func(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            heads = resp.headers

            heads['Access-Control-Allow-Origin'] = origin
            heads['Access-Control-Allow-Methods'] = get_methods()
            heads['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                heads['Access-Control-Allow-Headers'] = headers
            return resp

        func.provide_automatic_options = False
        return update_wrapper(wrapped_function, func)
    return decorator

URL1 = 'https://voat.co/api'
URL2 = 'https://fakevout.azurewebsites.net/api'

# Login Route

@app.route('/api/token', methods=['OPTIONS', 'POST'])
@crossdomain(origin='*', methods=['OPTIONS', 'POST'], headers=['Content-Type'])
def login():
    '''
     route for obtaining an authentication token for session storage.
    '''
    pay = loads(request.data)
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    return jsonify(post('%s/token' % URL2,
                        data={
                            'username': pay['username'],
                            'password': pay['password'],
                            'grant_type': 'password'
                        },
                        headers=headers).json())

# Non-Authorized Routes

@app.route('/api/posts/<subverse>/<page>/<search>')
@crossdomain(origin='*')
def frontpage(subverse, page, search):
    '''
     route for obtaining list of posts

     subverse (string) - subverse from which to obtain posts
     page     (string) - page from where posts are obtained
     search   (string) - query posts with matching string
    '''
    url = '%s/v1/v/%s?page=%s' % (URL2, subverse, page)
    if search != 'null':
        url += '&search=%s' % search
    return jsonify({'submissions': get(url, headers=headers).json()['data']})

@app.route('/api/post/<post_id>')
@crossdomain(origin='*')
def openpost(post_id):
    '''
     route for obtaining a specified post

     id (string) - id of post to obtain
    '''
    url = '%s/v1/submissions/%s' % (URL2, post_id)
    return jsonify({'submission': get(url, headers=headers).json()['data']})

@app.route('/api/user/<user>/<utype>')
@crossdomain(origin='*')
def userinfo(user, utype):
    '''
     route for obtaining user info, posts, or comments

     user  (string) - user from whom to obtain info
     utype (string) - which info to obtain (enum: info, submissions, comments)
    '''
    resp = get('%s/v1/u/%s/%s?sort=new' % (URL2, user, utype), headers=headers).json()['data']
    if isinstance(resp, list):
        resp = {'items': resp}
    return jsonify(resp)

@app.route('/api/comments/<subverse>/<post_id>')
@crossdomain(origin='*')
def comments(subverse, post_id):
    '''
     route for obtaining comments for a specified post

     subverse (string) - subverse that specified post belongs to
     id       (string) - id of post to obtain
    '''
    return jsonify({'comments': get('%s/v1/v/%s/%s/comments' % (URL2, subverse, post_id),
                                    headers=headers).json()['data']})

# Authorized Routes

# GET

@app.route('/api/messages/<mtype>/<state>', methods=['OPTIONS', 'GET'])
@crossdomain(origin='*', methods=['OPTIONS', 'GET'], headers=['Authorization'])
def messages(mtype, state):
    '''
     route for obtaining messages

     mtype (string) - type of messages to obtain (enum: inbox, sent, comment,
     submission, mention, all)
     state (string) - state of messages to obtain (enum: unread, read, all)
    '''
    url = '%s/v1/u/messages/%s/%s' % (URL2, mtype, state)
    headers['Authorization'] = 'Bearer %s' % request.headers['Authorization']
    return jsonify({'messages': get(url, headers=headers).json()['data']})

# POST

@app.route('/api/comment', methods=['OPTIONS', 'POST'])
@crossdomain(origin='*', methods=['OPTIONS', 'POST'], headers=['Content-Type', 'Authorization'])
def comment():
    '''
     route for commenting on a specified post

     subverse (string) - subverse of post to comment on
     postId   (string) - id of post to comment on
     comment  (string) - content of comment
    '''
    pay = loads(request.data)
    headers['Authorization'] = 'Bearer %s' % request.headers['Authorization']
    return jsonify(post('%s/v1/v/%s/%s/comment' % (URL2, pay['subverse'], pay['postId']),
                        data=dumps({
                            'value': pay['comment']
                        }),
                        headers=headers).json())

@app.route('/api/reply/comment', methods=['OPTIONS', 'POST'])
@crossdomain(origin='*', methods=['OPTIONS', 'POST'], headers=['Content-Type', 'Authorization'])
def commentreply():
    '''
     route for replying to specified comment

     subverse  (string) - subverse of comment reply
     postId    (string) - id of post of comment reply
     commentId (string) - id of parent comment of reply
     content   (string) - content of reply
    '''
    pay = loads(request.data)
    headers['Authorization'] = 'Bearer %s' % request.headers['Authorization']
    url = '%s/v1/v/%s/%s/comment/%s' % (URL2, pay['subverse'], pay['postId'], pay['commentId'])
    data = dumps({'value': pay['content']})
    return jsonify(post(url, data=data, headers=headers).json())

@app.route('/api/reply/message', methods=['OPTIONS', 'POST'])
@crossdomain(origin='*', methods=['OPTIONS', 'POST'], headers=['Content-Type', 'Authorization'])
def messagereply():
    '''
     route for replying to message

     content (string) - content of message
     id      (string) - id of message to reply
    '''
    pay = loads(request.data)
    headers['Authorization'] = 'Bearer %s' % request.headers['Authorization']
    data = dumps({'value': pay['content']})
    return jsonify(post('%s/v1/u/messages/reply/%s' % (URL2, pay['id']),
                        data=data, headers=headers).json())

@app.route('/api/vote', methods=['OPTIONS', 'POST'])
@crossdomain(origin='*', methods=['OPTIONS', 'POST'], headers=['Content-Type', 'Authorization'])
@crossdomain(origin='*')
def vote():
    '''
     route for voting on a comment or post

     type (string) - type of vote (enum: submission, comment)
     id   (string) - id of submission/comment to vote on
     vote (string) - value of vote (enum: 1, 0, -1)
    '''
    pay = loads(request.data)
    headers['Authorization'] = 'Bearer %s' % request.headers['Authorization']
    return jsonify(post('%s/v1/vote/%s/%s/%s' % (URL2, pay['type'], pay['id'], pay['vote']),
                        headers=headers).json())

@app.route('/api/save', methods=['OPTIONS', 'POST'])
@crossdomain(origin='*', methods=['OPTIONS', 'POST'], headers=['Content-Type', 'Authorization'])
def save():
    '''
     route to save a post or comment

     type (string) - type of save (enum: submissions, comments)
     id   (string) - id of submission/comment to save
    '''
    pay = loads(request.data)
    headers['Authorization'] = 'Bearer %s' % request.headers['Authorization']
    return jsonify(post('%s/v1/%s/%s/save' % (URL2, pay['type'], pay['id']),
                        headers=headers).json())

@app.route('/api/post', methods=['OPTIONS', 'POST'])
@crossdomain(origin='*', methods=['OPTIONS', 'POST'], headers=['Content-Type', 'Authorization'])
def submit_post():
    '''
     route to submit a post

     title    (string) - title of post
     subverse (string) - subverse to post on
     url      (string) - url to post (either url or content is required)
     content  (string) - content of post (ignored if url is specified)
    '''
    pay = loads(request.data)
    headers['Authorization'] = 'Bearer %s' % request.headers['Authorization']
    data = {
        'title': pay['title']
    }
    if 'url' in pay:
        data['url'] = pay['url']
    else:
        data['content'] = pay['content']
    return jsonify(post('%s/v1/v/%s' % (URL2, pay['subverse']),
                        data=dumps(data),
                        headers=headers).json())

# DELETE

@app.route('/api/delete', methods=['OPTIONS', 'DELETE'])
@crossdomain(origin='*', methods=['OPTIONS', 'DELETE'], headers=['Content-Type', 'Authorization'])
def delete_something():
    '''
     route for deleting a post/comment

     type (string) - type of delete (enum: submissions, comments)
     id   (string) - id of post/comment to delete
    '''
    pay = loads(request.data)
    headers['Authorization'] = 'Bearer %s' % request.headers['Authorization']
    return jsonify(delete('%s/v1/%s/%s' % (URL2, pay['type'], pay['id']),
                          headers=headers).json())

# PUT

@app.route('/api/edit', methods=['OPTIONS', 'PUT'])
@crossdomain(origin='*', methods=['OPTIONS', 'PUT'], headers=['Content-Type', 'Authorization'])
def edit():
    '''
     route for editing a post or comment

     type    (string) - type of edit (enum: submissions, comments)
     content (string) - content of edit
     id      (string) - id of post/comment to edit
    '''
    pay = loads(request.data)
    headers['Authorization'] = 'Bearer %s' % request.headers['Authorization']
    data = {}
    if pay['type'] == 'comments':
        data['value'] = pay['content']
    else:
        data['content'] = pay['content']
    return jsonify(put('%s/v1/%s/%s' % (URL2, pay['type'], pay['id']),
                       data=dumps(data), headers=headers).json())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
