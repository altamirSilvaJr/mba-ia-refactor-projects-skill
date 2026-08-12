class TaskController:
    def __init__(self, service):
        self.service = service

    def list(self): return self.service.list_tasks(), 200
    def get(self, task_id): return self.service.get_task(task_id), 200
    def create(self, data): return self.service.create_task(data), 201
    def update(self, task_id, data): return self.service.update_task(task_id, data), 200
    def delete(self, task_id): return self.service.delete_task(task_id), 200
    def search(self, args): return self.service.search_tasks(args), 200
    def stats(self): return self.service.stats(), 200

