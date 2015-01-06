from app import app, db, login_manager
from datetime import datetime
from passlib.apps import custom_app_context as pwd_context


roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return '<Role: %s>' % self.name


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('User', lazy='dynamic'))

    def __init__(self, email, username, password):
        # Normalize the email by stripping whitespace and lowercasing
        self.email = email.strip().lower()
        self.username = username
        # Hash the password
        self.hash_password(password)
        # Give the new user a default role, make sure to create this role first
        default_role = Role.query.filter_by(name=app.config['DEFAULT_ROLE']).first()
        self.roles.append(default_role)
        self.active = True
        self.created_at = datetime.utcnow()

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User: %s>' % self.email


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class SendbackAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stellar_name = db.Column(db.Text)
    stellar_address = db.Column(db.Text)
    destination_tag = db.Column(db.Integer)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)
    transactions = db.relationship('SendbackTransaction', backref='SendbackAccount', lazy='dynamic')
    payables = db.relationship('Payable', backref='SendbackAccount', lazy='dynamic')

    def __repr__(self):
        return '<SendbackAccount: %s>' % self.stellar_name


class SendbackTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    sendback_account = db.Column(db.Integer, db.ForeignKey(SendbackAccount.id))

    account_sender = db.Column(db.Text)
    amount_sender = db.Column(db.Integer)
    destination_sender = db.Column(db.Text)
    destination_tag_sender = db.Column(db.Integer)
    fee_sender = db.Column(db.Integer)
    flags_sender = db.Column(db.Text)
    sequence_sender = db.Column(db.Text)
    signing_pub_key_sender = db.Column(db.Text)
    transaction_type_sender = db.Column(db.Text)
    tx_signature_sender = db.Column(db.Text)
    tx_hash_sender = db.Column(db.Text)
    ledger_index_sender = db.Column(db.Text)
    date_sender = db.Column(db.Text)
    ledger_hash_sender = db.Column(db.Text)
    validated_sender = db.Column(db.Boolean)

    payable = db.relationship('Payable', backref='SendbackTransaction', lazy='dynamic')

    def __repr__(self):
        return '<Transaction: %s - %s>' % (self.account, self.amount)


class Payable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    destination = db.Column(db.Text)
    amount = db.Column(db.Integer)
    sendback_transaction = db.Column(db.Integer, db.ForeignKey(SendbackTransaction.id))
    sendback_account = db.Column(db.Integer, db.ForeignKey(SendbackAccount.id))
    pending_transaction = db.relationship('PendingTransaction', backref='Payable', lazy='dynamic')
    tx_signed = db.Column(db.Boolean)
    tx_submitted = db.Column(db.Boolean)
    tx_validated = db.Column(db.Boolean)

    tx_blob = db.Column(db.Text)
    tx_hash = db.Column(db.Text)

    account_fulfilled = db.Column(db.Text)
    amount_fulfilled = db.Column(db.Integer)
    destination_fulfilled = db.Column(db.Text)
    destination_tag_fulfilled = db.Column(db.Integer)
    fee_fulfilled = db.Column(db.Integer)
    flags_fulfilled = db.Column(db.Text)
    sequence_fulfilled = db.Column(db.Text)
    signing_pub_key_fulfilled = db.Column(db.Text)
    transaction_type_fulfilled = db.Column(db.Text)
    tx_signature_fulfilled = db.Column(db.Text)
    tx_hash_fulfilled = db.Column(db.Text)
    date_fulfilled = db.Column(db.Text)
    ledger_hash_fulfilled = db.Column(db.Text)
    ledger_index_fulfilled = db.Column(db.Text)

    def __repr__(self):
        return '<Payable: %s>' % self.id


class PendingTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.Text)
    amount = db.Column(db.Integer)
    created_time = db.Column(db.DateTime)
    payable = db.Column(db.Integer, db.ForeignKey(Payable.id))
    tx_signed = db.Column(db.Boolean)
    tx_submitted = db.Column(db.Boolean)
    tx_validated = db.Column(db.Boolean)
    sequence = db.Column(db.Integer)

    tx_blob = db.Column(db.Text)
    tx_hash = db.Column(db.Text)















