class UserController:
    def __init__(self, service):
        self.service = service

    def list(self): return self.service.list_users(), 200
    def get(self, user_id): return self.service.get_user(user_id), 200
    def create(self, data): return self.service.create_user(data), 201
    def update(self, user_id, data, can_change_role=False): return self.service.update_user(user_id, data, can_change_role), 200
    def delete(self, user_id): return self.service.delete_user(user_id), 200
    def tasks(self, user_id): return self.service.user_tasks(user_id), 200
    def login(self, data): return self.service.login(data), 200

