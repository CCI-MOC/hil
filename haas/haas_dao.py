session = None
def init_session(s):
    global session
    session = s
def get(cls, label):
    return session.query(cls).filter_by(label=label).all()
def save(e):
    session.add(e)
    session.commit()
