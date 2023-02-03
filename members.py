class Members:

    def populate(self, members):
        self.members = members

    def getUserID(self, email):
        if email is not None:
            for member in self.members:
                if member["email"] == email:
                    return member["user"]["id"]
        return None

    def print(self):
        print(self.members)