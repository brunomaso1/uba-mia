import typer
from vision_transformer.flows import dataset_flow, train_flow, evaluate_flow
from vision_transformer.utils import DatasetFormat

app = typer.Typer(help="CLI para ejecución de flujos de trabajo utilizando Prefect")

@app.command()
def prepare_dataset_flow(fmt: DatasetFormat):
    dataset_flow.execute_flow(format=fmt)

@app.command()
def train_flow(epochs: int = 10):
    train_flow.execute_flow()

@app.command()
def evaluate_flow():
    evaluate_flow.execute_flow()

if __name__ == "__main__":
    app()