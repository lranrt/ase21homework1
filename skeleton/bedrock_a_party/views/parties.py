from flakon import JsonBlueprint
from flask import abort, jsonify, request

from bedrock_a_party.classes.party import CannotPartyAloneError, ItemAlreadyInsertedByUser, NotExistingFoodError, NotInvitedGuestError, Party

parties = JsonBlueprint('parties', __name__)

_LOADED_PARTIES = {}  # dict of available parties
_PARTY_NUMBER = 0  # index of the last created party


@parties.route("/parties", methods=['GET', 'POST'])
def all_parties():
    if request.method == 'POST':
        try:
            # creates a party and returns the party ID
            result = create_party(request)

        except CannotPartyAloneError as e:
            # returns error 400
            abort(400, str(e))

    elif request.method == 'GET':
        # gets all the parties
        result = get_all_parties()

    return result


@parties.route("/parties/loaded")
def loaded_parties():
    # returns the number of parties currently loaded in the system
    loaded_parties = len(_LOADED_PARTIES)
    return jsonify({'loaded_parties': loaded_parties})


@parties.route("/party/<id>", methods=['GET', 'DELETE'])
def single_party(id):
    global _LOADED_PARTIES
    result = ""

    # checks if the party is an existing one in loaded parties list
    exists_party(id)
    # if the party exists, then it proceeds
    if 'GET' == request.method:
        # retrieves a party from the loaded parties list
        requested_party = requested_party=_LOADED_PARTIES.get(id).serialize()
        result = jsonify(requested_party)

    elif 'DELETE' == request.method:
        # deletes a party from the loaded parties list
        del _LOADED_PARTIES[id]
        result = jsonify(msg ='the requested party has been deleted!')

    return result


@parties.route("/party/<id>/foodlist")
def get_foodlist(id):
    global _LOADED_PARTIES
    result = ""

    # checks if the party is an existing one in loaded parties list
    exists_party(id)
    # if the party exists, then it proceeds
    if 'GET' == request.method:
        # retrieves food-list of the party
        party = _LOADED_PARTIES.get(id)
        requested_food = party.get_food_list().serialize()
        result = jsonify({'foodlist': requested_food})

    return result

@parties.route("/party/<id>/foodlist/<user>/<item>", methods = ['POST', 'DELETE'])
def edit_foodlist(id, user, item):
    global _LOADED_PARTIES

    # checks if the party is an existing one in loaded parties list
    exists_party(id)
    result = ""

    # if the party exists, then it proceeds
    # retrieves the party
    party = _LOADED_PARTIES.get(id)

    if 'POST' == request.method:
        # adds item to food-list handling NotInvitedGuestError (401) and ItemAlreadyInsertedByUser (400)
        try:
            party.add_to_food_list(item, user)
            result = jsonify({'food': item,
                              'user': user})
        except NotInvitedGuestError as e:
            abort(401, str(e))
        except ItemAlreadyInsertedByUser as e:
            abort(400, str(e))

    if 'DELETE' == request.method:
        # deletes item to food-list handling NotExistingFoodError (400)
        try: 
            party.remove_from_food_list(item, user)
            result = jsonify(msg = 'Food deleted!')
        except NotExistingFoodError as e:
            abort(400, str(e))

    return result


#
# These are utility functions. Use them, DON'T CHANGE THEM!!
#

def create_party(req):
    global _LOADED_PARTIES, _PARTY_NUMBER

    # get data from request
    json_data = req.get_json()

    # list of guests
    try:
        guests = json_data['guests']
    except:
        raise CannotPartyAloneError("you cannot party alone!")

    # add party to the loaded parties lists
    _LOADED_PARTIES[str(_PARTY_NUMBER)] = Party(_PARTY_NUMBER, guests)
    _PARTY_NUMBER += 1

    return jsonify({'party_number': _PARTY_NUMBER - 1})


def get_all_parties():
    global _LOADED_PARTIES

    return jsonify(loaded_parties=[party.serialize() for party in _LOADED_PARTIES.values()])


def exists_party(_id):
    global _PARTY_NUMBER
    global _LOADED_PARTIES

    if int(_id) > _PARTY_NUMBER:
        abort(404)  # error 404: Not Found, i.e. wrong URL, resource does not exist
    elif not(_id in _LOADED_PARTIES):
        abort(410)  # error 410: Gone, i.e. it existed but it's not there anymore
