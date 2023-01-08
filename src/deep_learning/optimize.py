from pathlib import Path

import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint, LearningRateMonitor
from pytorch_lightning.loggers import WandbLogger
#from tsai.all import *

#from tsai.models.TransformerPlus import TransformerPlus
from tsai.models.FCNPlus import FCNPlus
from tsai.models.ResNetPlus import ResNetPlus
from tsai.models.XceptionTimePlus import XceptionTimePlus
from tsai.models.RNNPlus import GRUPlus, LSTMPlus, RNNPlus
from tsai.models.TSSequencerPlus import TSSequencerPlus
from tsai.models.XResNet1dPlus import xresnet1d50_deeperplus
from tsai.models.InceptionTimePlus import InceptionTimePlus
from tsai.models.RNN_FCNPlus import MGRU_FCNPlus, MLSTM_FCNPlus, MRNN_FCNPlus

from torchvision import transforms
import torch


from src.deep_learning.data.datamodule import DataModule
from src.deep_learning.models.lightning_module import LightningModule
from src.deep_learning.transforms.common import ZScoreNormalize, L2Normalize

import optuna
class HyperparameterOptimization:

    def __init__(self, root_data_dir):
        self.root_data_dir = root_data_dir

    def objective(self,trial):
        """
        Objective function to be optimized.
        """

        # Create datamodule
        BATCH_SIZE = trial.suggest_int("batch_size", 32, 256)
        print("Batch size:", BATCH_SIZE)
        # BATCH_SIZE = 32
        BATCH_SIZE = 500

        # define transforms {"train": , "valid": None, "test": None}
        tsfm = {"train": transforms.Compose([ZScoreNormalize(), L2Normalize()]), 
            "valid": transforms.Compose([ZScoreNormalize(), L2Normalize()]), 
            "test": transforms.Compose([ZScoreNormalize(), L2Normalize()])}

        dm = DataModule(self.root_data_dir, batch_size=BATCH_SIZE, transforms=tsfm, balanced=True)

        # Choose model

        MODEL_NAME = trial.suggest_categorical("model", ["FCNPlus", "ResNetPlus", "XceptionTimePlus", "GRUPlus", "LSTMPlus", "RNNPlus", "TSSequencerPlus", "xresnet1d50_deeperplus", "InceptionTimePlus", "MGRU_FCNPlus", "MLSTM_FCNPlus", "MRNN_FCNPlus"])
        print("Model:", MODEL_NAME)
        # MODEL_NAME = "xresnet1d50_deeperplus"
        if MODEL_NAME == "FCNPlus":
            model = FCNPlus(21, 2)
        elif MODEL_NAME == "ResNetPlus":
            model = ResNetPlus(21, 2)
        elif MODEL_NAME == "XceptionTimePlus":
            model = XceptionTimePlus(21, 2)
        elif MODEL_NAME == "GRUPlus":
            model = GRUPlus(21, 2)
        elif MODEL_NAME == "LSTMPlus":
            model = LSTMPlus(21, 2)
        elif MODEL_NAME == "RNNPlus":
            model = RNNPlus(21, 2)
        elif MODEL_NAME == "TSSequencerPlus":
            model = TSSequencerPlus(21, 2, 128)
        elif MODEL_NAME == "xresnet1d50_deeperplus":
            model = xresnet1d50_deeperplus(21, 2)
        elif MODEL_NAME == "InceptionTimePlus":
            model = InceptionTimePlus(21, 2)
        elif MODEL_NAME == "MGRU_FCNPlus":
            model = MGRU_FCNPlus(21, 2, 128)
        elif MODEL_NAME == "MLSTM_FCNPlus":
            model = MLSTM_FCNPlus(21, 2, 128)
        elif MODEL_NAME == "MRNN_FCNPlus":
            model = MRNN_FCNPlus(21, 2, 128)
        else:
            raise ValueError("Invalid model name.")

        # Create LightningModule
        num_classes = 2
        LEARNING_RATE = trial.suggest_loguniform("learning_rate", 1e-4, 1e-2)
        model = LightningModule(model, num_classes=num_classes, learning_rate=LEARNING_RATE)

        # Logger
        wandb_logger = WandbLogger(project='epileptic-detection', job_type='train')

        # Callbacks
        callbacks = [
            # EarlyStopping(monitor="val_loss", min_delta=0.00, patience=3, verbose=False, mode="max"),
            #LearningRateMonitor(),
            #ModelCheckpoint(dirpath="./checkpoints", monitor="val_loss", filename="model_{epoch:02d}_{val_loss:.2f}")
        ]

        # Create trainer
        trainer = pl.Trainer(max_epochs=5,#max_steps=10000,
                             check_val_every_n_epoch=None,
                             gpus=1,
                             logger=wandb_logger,
                             callbacks=callbacks,
                             enable_progress_bar=True,
                             accelerator="gpu")

        trainer.fit(model, dm)

        return model.min_loss

if __name__ == "__main__":
    root_data_dir = Path("../data/").resolve()
    opt = HyperparameterOptimization(root_data_dir)
    study = optuna.create_study(direction="minimize")
    study.optimize(opt.objective, n_trials=1)
    print(study.best_trial)
    
