from locust import HttpUser, between, task


class JobTrackerUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def health_check(self):
        self.client.get("/api/health")