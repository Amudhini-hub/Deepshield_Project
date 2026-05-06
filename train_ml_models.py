#!/usr/bin/env python3
"""
DeepShield ML Model Training Pipeline
Trains and validates deepfake detection and liveness detection models
"""

import os
import sys
import logging
from pathlib import Path
import numpy as np
import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.config.config import get_config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

config = get_config()

class ModelTrainer:
    """ML Model Training Orchestrator"""

    def __init__(self):
        self.models_dir = Path("ml_models")
        self.deepfake_dir = self.models_dir / "deepfake_detection"
        self.liveness_dir = self.models_dir / "liveness_detection"

        # Create directories
        self.deepfake_dir.mkdir(parents=True, exist_ok=True)
        self.liveness_dir.mkdir(parents=True, exist_ok=True)

        # Training parameters
        self.batch_size = 32
        self.epochs = 50
        self.validation_split = 0.2
        self.learning_rate = 0.001

    def generate_synthetic_data(self, num_samples=1000, img_size=(224, 224)):
        """Generate synthetic training data for demonstration"""
        logger.info(f"Generating {num_samples} synthetic samples...")

        # Generate random images (in practice, use real datasets)
        X = []
        y = []

        for i in range(num_samples):
            # Create random image
            img = np.random.randint(0, 255, (*img_size, 3), dtype=np.uint8)

            # Random label (0=real, 1=fake for deepfake; 0=not_alive, 1=alive for liveness)
            label = np.random.choice([0, 1])

            X.append(img)
            y.append(label)

        X = np.array(X, dtype=np.float32) / 255.0  # Normalize
        y = np.array(y, dtype=np.int32)

        logger.info(f"Generated dataset: {X.shape}, labels: {y.shape}")
        return X, y

    def build_deepfake_model(self, input_shape=(224, 224, 3)):
        """Build deepfake detection model"""
        logger.info("Building deepfake detection model...")

        model = keras.Sequential([
            keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=input_shape),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Conv2D(64, (3, 3), activation='relu'),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Conv2D(128, (3, 3), activation='relu'),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Flatten(),
            keras.layers.Dense(128, activation='relu'),
            keras.layers.Dropout(0.5),
            keras.layers.Dense(1, activation='sigmoid')
        ])

        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.AUC(name='auc')]
        )

        return model

    def build_liveness_model(self, input_shape=(224, 224, 3)):
        """Build liveness detection model"""
        logger.info("Building liveness detection model...")

        model = keras.Sequential([
            keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=input_shape),
            keras.layers.BatchNormalization(),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Conv2D(64, (3, 3), activation='relu'),
            keras.layers.BatchNormalization(),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Conv2D(128, (3, 3), activation='relu'),
            keras.layers.BatchNormalization(),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Flatten(),
            keras.layers.Dense(256, activation='relu'),
            keras.layers.Dropout(0.5),
            keras.layers.Dense(128, activation='relu'),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(1, activation='sigmoid')
        ])

        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.AUC(name='auc'), keras.metrics.Precision(), keras.metrics.Recall()]
        )

        return model

    def train_model(self, model, X_train, y_train, X_val, y_val, model_name, model_dir):
        """Train a model with callbacks and monitoring"""
        logger.info(f"Training {model_name}...")

        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_auc',
                patience=10,
                restore_best_weights=True,
                mode='max'
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_auc',
                factor=0.5,
                patience=5,
                min_lr=1e-6,
                mode='max'
            ),
            keras.callbacks.ModelCheckpoint(
                filepath=str(model_dir / f"{model_name}_best.h5"),
                monitor='val_auc',
                save_best_only=True,
                mode='max'
            )
        ]

        # Train
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=self.epochs,
            batch_size=self.batch_size,
            callbacks=callbacks,
            verbose=1
        )

        # Save final model
        model_path = model_dir / f"{model_name}_final.h5"
        model.save(str(model_path))
        logger.info(f"Model saved to {model_path}")

        return model, history

    def evaluate_model(self, model, X_test, y_test, model_name):
        """Evaluate model performance"""
        logger.info(f"Evaluating {model_name}...")

        # Predictions
        y_pred_prob = model.predict(X_test)
        y_pred = (y_pred_prob > 0.5).astype(int).flatten()

        # Classification report
        report = classification_report(y_test, y_pred, target_names=['Negative', 'Positive'])
        logger.info(f"\n{model_name} Classification Report:\n{report}")

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        logger.info(f"Confusion Matrix:\n{cm}")

        # Calculate metrics
        accuracy = np.mean(y_pred == y_test)
        precision = np.sum((y_pred == 1) & (y_test == 1)) / np.sum(y_pred == 1) if np.sum(y_pred == 1) > 0 else 0
        recall = np.sum((y_pred == 1) & (y_test == 1)) / np.sum(y_test == 1) if np.sum(y_test == 1) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        metrics = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1)
        }

        logger.info(f"{model_name} Metrics: {metrics}")
        return metrics

    def plot_training_history(self, history, model_name, model_dir):
        """Plot training history"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))

        # Accuracy
        ax1.plot(history.history['accuracy'], label='Train')
        ax1.plot(history.history['val_accuracy'], label='Validation')
        ax1.set_title('Model Accuracy')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Accuracy')
        ax1.legend()

        # Loss
        ax2.plot(history.history['loss'], label='Train')
        ax2.plot(history.history['val_loss'], label='Validation')
        ax2.set_title('Model Loss')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Loss')
        ax2.legend()

        # AUC
        if 'auc' in history.history:
            ax3.plot(history.history['auc'], label='Train')
            ax3.plot(history.history['val_auc'], label='Validation')
            ax3.set_title('Model AUC')
            ax3.set_xlabel('Epoch')
            ax3.set_ylabel('AUC')
            ax3.legend()

        # Learning Rate
        if hasattr(history, 'lr') and history.lr is not None:
            ax4.plot(history.lr, label='Learning Rate')
            ax4.set_title('Learning Rate')
            ax4.set_xlabel('Epoch')
            ax4.set_ylabel('Learning Rate')
            ax4.set_yscale('log')
            ax4.legend()

        plt.tight_layout()
        plot_path = model_dir / f"{model_name}_training_history.png"
        plt.savefig(str(plot_path))
        plt.close()
        logger.info(f"Training plot saved to {plot_path}")

    def save_model_metadata(self, model_name, metrics, model_dir, training_time):
        """Save model metadata"""
        metadata = {
            'model_name': model_name,
            'training_date': datetime.now().isoformat(),
            'training_time_seconds': training_time,
            'metrics': metrics,
            'hyperparameters': {
                'batch_size': self.batch_size,
                'epochs': self.epochs,
                'learning_rate': self.learning_rate,
                'validation_split': self.validation_split
            },
            'framework': 'TensorFlow/Keras',
            'version': tf.__version__
        }

        metadata_path = model_dir / f"{model_name}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Model metadata saved to {metadata_path}")

    def train_deepfake_model(self):
        """Train deepfake detection model"""
        logger.info("Starting deepfake detection model training...")

        # Generate synthetic data
        X, y = self.generate_synthetic_data(2000, img_size=(224, 224))

        # Split data
        X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
        X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

        # Build model
        model = self.build_deepfake_model()

        # Train
        start_time = datetime.now()
        trained_model, history = self.train_model(model, X_train, y_train, X_val, y_val,
                                                "deepfake_detector", self.deepfake_dir)
        training_time = (datetime.now() - start_time).total_seconds()

        # Evaluate
        metrics = self.evaluate_model(trained_model, X_test, y_test, "Deepfake Detection")

        # Plot history
        self.plot_training_history(history, "deepfake_detector", self.deepfake_dir)

        # Save metadata
        self.save_model_metadata("deepfake_detector", metrics, self.deepfake_dir, training_time)

        logger.info("Deepfake detection model training completed!")
        return trained_model, metrics

    def train_liveness_model(self):
        """Train liveness detection model"""
        logger.info("Starting liveness detection model training...")

        # Generate synthetic data
        X, y = self.generate_synthetic_data(2000, img_size=(224, 224))

        # Split data
        X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
        X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

        # Build model
        model = self.build_liveness_model()

        # Train
        start_time = datetime.now()
        trained_model, history = self.train_model(model, X_train, y_train, X_val, y_val,
                                                "liveness_detector", self.liveness_dir)
        training_time = (datetime.now() - start_time).total_seconds()

        # Evaluate
        metrics = self.evaluate_model(trained_model, X_test, y_test, "Liveness Detection")

        # Plot history
        self.plot_training_history(history, "liveness_detector", self.liveness_dir)

        # Save metadata
        self.save_model_metadata("liveness_detector", metrics, self.liveness_dir, training_time)

        logger.info("Liveness detection model training completed!")
        return trained_model, metrics

    def run_training_pipeline(self):
        """Run complete training pipeline"""
        logger.info("🚀 Starting DeepShield ML Model Training Pipeline")
        logger.info("=" * 60)

        try:
            # Train deepfake detection model
            deepfake_model, deepfake_metrics = self.train_deepfake_model()

            # Train liveness detection model
            liveness_model, liveness_metrics = self.train_liveness_model()

            # Summary
            logger.info("=" * 60)
            logger.info("🎉 TRAINING PIPELINE COMPLETED!")
            logger.info("=" * 60)
            logger.info(f"Deepfake Detection - Accuracy: {deepfake_metrics['accuracy']:.3f}")
            logger.info(f"Liveness Detection - Accuracy: {liveness_metrics['accuracy']:.3f}")
            logger.info("Models saved to ml_models/ directory")
            logger.info("Ready for deployment!")

            return True

        except Exception as e:
            logger.error(f"Training pipeline failed: {e}")
            return False

def main():
    """Main training function"""
    trainer = ModelTrainer()
    success = trainer.run_training_pipeline()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)