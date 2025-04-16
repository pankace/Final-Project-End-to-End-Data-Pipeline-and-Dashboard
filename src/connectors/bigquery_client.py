from google.cloud import bigquery

class BigQueryClient:
    def __init__(self, project_id, dataset_id):
        self.client = bigquery.Client(project=project_id)
        self.dataset_id = dataset_id

    def insert_rows(self, table_id, rows):
        table_ref = self.client.dataset(self.dataset_id).table(table_id)
        errors = self.client.insert_rows_json(table_ref, rows)
        return errors

    def query(self, query_string):
        query_job = self.client.query(query_string)
        return query_job.result()

    def create_table(self, table_id, schema):
        table_ref = self.client.dataset(self.dataset_id).table(table_id)
        table = bigquery.Table(table_ref, schema=schema)
        table = self.client.create_table(table)
        return table

    def delete_table(self, table_id):
        table_ref = self.client.dataset(self.dataset_id).table(table_id)
        self.client.delete_table(table_ref, not_found_ok=True)