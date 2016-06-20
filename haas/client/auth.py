import base64



def auth_db(username, password):
    concatit = username+":"+password
    concatit64 = base64.b64encode(concatit)

    return concatit64




