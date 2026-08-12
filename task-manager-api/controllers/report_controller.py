class ReportController:
    def __init__(self, service):
        self.service = service

    def summary(self): return self.service.summary(), 200
    def user(self, user_id): return self.service.user_report(user_id), 200
    def categories(self): return self.service.list_categories(), 200
    def create_category(self, data): return self.service.create_category(data), 201
    def update_category(self, category_id, data): return self.service.update_category(category_id, data), 200
    def delete_category(self, category_id): return self.service.delete_category(category_id), 200

