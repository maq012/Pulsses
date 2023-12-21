from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

jwt = JWTManager()
migrate = Migrate()
blocklist = set()


@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    return jti in blocklist


def blacklist_token(jti):
    blocklist.add(jti)
    return True