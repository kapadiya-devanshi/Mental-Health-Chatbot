"""
Model Training Script for SoulMate Chatbot
Trains the neural network using intents.json and self-learning data
"""

import json
import pickle
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from keras.models import Sequential
from keras.layers import Dense, Dropout, BatchNormalization
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from keras.models import load_model
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
import random
import os
from datetime import datetime

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INTENTS_FILE = os.path.join(BASE_DIR, "..", "static", "data", "intents.json")
LEARNING_DATA_FILE = os.path.join(BASE_DIR, "..", "static", "data", "learning_data.json")
MODEL_FILE = os.path.join(BASE_DIR, "..", "..", "chatbot-model.h5")
DATA_PICKLE = os.path.join(BASE_DIR, "..", "..", "data.pickle")


class ChatbotTrainer:
    """Trainer class for the chatbot neural network model"""
    
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.words = []
        self.classes = []
        self.documents = []
        self.ignore_letters = ['?', '!', '.', ',']
        self.model = None
        self.training_data = None
        
    def load_intents(self):
        """Load intents from JSON file"""
        try:
            with open(INTENTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading intents: {e}")
            return {"intents": []}
    
    def load_learning_data(self):
        """Load self-learning data"""
        try:
            with open(LEARNING_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
    
    def tokenize_and_lemmatize(self, sentence):
        """Tokenize and lemmatize a sentence"""
        sentence_words = nltk.word_tokenize(sentence.lower())
        sentence_words = [self.lemmatizer.lemmatize(word) 
                         for word in sentence_words 
                         if word not in self.ignore_letters]
        return sentence_words
    
    def create_training_data(self, intents_data, learning_data=None):
        """Create training data from intents and learning data"""
        self.words = []
        self.classes = []
        self.documents = []
        
        # Process intents
        for intent in intents_data.get("intents", []):
            tag = intent["tag"]
            
            # Add to classes if new
            if tag not in self.classes:
                self.classes.append(tag)
            
            # Process patterns
            for pattern in intent.get("patterns", []):
                # Tokenize
                words = self.tokenize_and_lemmatize(pattern)
                self.words.extend(words)
                self.documents.append((words, tag))
        
        # Add learning data if available
        if learning_data:
            # Add user patterns
            for pattern, data in learning_data.get("user_patterns", {}).items():
                tag = data.get("intent_tag", "unknown")
                if tag in self.classes:
                    words = self.tokenize_and_lemmatize(pattern)
                    self.words.extend(words)
                    self.documents.append((words, tag))
            
            # Add new patterns
            for pattern, data in learning_data.get("new_patterns", {}).items():
                tag = data.get("intent_tag", "unknown")
                if tag in self.classes:
                    words = self.tokenize_and_lemmatize(pattern)
                    self.words.extend(words)
                    self.documents.append((words, tag))
        
        # Sort and deduplicate
        self.words = sorted(list(set(self.words)))
        self.classes = sorted(list(set(self.classes)))
        
        print(f"Words: {len(self.words)}")
        print(f"Classes: {len(self.classes)}")
        print(f"Documents: {len(self.documents)}")
        
        return self.words, self.classes, self.documents
    
    def create_training_arrays(self):
        """Create training arrays (bag of words)"""
        training = []
        output_empty = [0] * len(self.classes)
        
        for doc in self.documents:
            bag = []
            word_patterns = doc[0]
            
            # Create bag of words
            for word in self.words:
                bag.append(1) if word in word_patterns else bag.append(0)
            
            # Create output row
            output_row = list(output_empty)
            output_row[self.classes.index(doc[1])] = 1
            
            training.append([bag, output_row])
        
        # Shuffle training data
        random.shuffle(training)
        
        # Convert to numpy arrays
        training = np.array(training, dtype=object)
        
        train_x = np.array(list(training[:, 0]))
        train_y = np.array(list(training[:, 1]))
        
        return train_x, train_y
    
    def create_model(self, input_shape, output_shape):
        """Create the neural network model"""
        model = Sequential([
            # Input layer
            Dense(256, input_shape=(input_shape,), activation='relu'),
            BatchNormalization(),
            Dropout(0.3),
            
            # Hidden layers
            Dense(128, activation='relu'),
            BatchNormalization(),
            Dropout(0.3),
            
            Dense(64, activation='relu'),
            BatchNormalization(),
            Dropout(0.3),
            
            # Output layer
            Dense(output_shape, activation='softmax')
        ])
        
        # Compile model
        optimizer = Adam(learning_rate=0.001)
        model.compile(
            optimizer=optimizer,
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train(self, epochs=200, batch_size=5, validation_split=0.2):
        """Train the model"""
        print("=" * 60)
        print("SoulMate Chatbot Model Training")
        print("=" * 60)
        
        # Load data
        print("\n1. Loading intents and learning data...")
        intents_data = self.load_intents()
        learning_data = self.load_learning_data()
        
        # Create training data
        print("\n2. Creating training data...")
        self.create_training_data(intents_data, learning_data)
        
        # Create training arrays
        print("\n3. Creating training arrays...")
        train_x, train_y = self.create_training_arrays()
        
        print(f"Training samples: {len(train_x)}")
        print(f"Features: {len(train_x[0])}")
        print(f"Classes: {len(train_y[0])}")
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            train_x, train_y, test_size=validation_split, random_state=42
        )
        
        # Create model
        print("\n4. Creating neural network model...")
        self.model = self.create_model(len(train_x[0]), len(train_y[0]))
        self.model.summary()
        
        # Callbacks
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=20,
                restore_best_weights=True,
                verbose=1
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=10,
                min_lr=0.00001,
                verbose=1
            )
        ]
        
        # Train model
        print(f"\n5. Training model (epochs={epochs}, batch_size={batch_size})...")
        print("-" * 60)
        
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_val, y_val),
            callbacks=callbacks,
            verbose=1
        )
        
        # Evaluate
        print("\n6. Evaluating model...")
        loss, accuracy = self.model.evaluate(X_val, y_val, verbose=0)
        print(f"Validation Loss: {loss:.4f}")
        print(f"Validation Accuracy: {accuracy:.4f}")
        
        # Save model
        print("\n7. Saving model...")
        self.model.save(MODEL_FILE)
        print(f"Model saved to: {MODEL_FILE}")
        
        # Save pickle data
        print("\n8. Saving training data...")
        self.training_data = {
            "words": self.words,
            "classes": self.classes,
            "train_x": train_x,
            "train_y": train_y,
            "history": history.history
        }
        
        with open(DATA_PICKLE, "wb") as f:
            pickle.dump(self.training_data, f)
        print(f"Training data saved to: {DATA_PICKLE}")
        
        # Save training info
        training_info = {
            "timestamp": datetime.now().isoformat(),
            "epochs_trained": len(history.history['loss']),
            "final_loss": float(history.history['loss'][-1]),
            "final_accuracy": float(history.history['accuracy'][-1]),
            "val_loss": float(history.history['val_loss'][-1]),
            "val_accuracy": float(history.history['val_accuracy'][-1]),
            "num_words": len(self.words),
            "num_classes": len(self.classes),
            "num_training_samples": len(train_x)
        }
        
        info_file = os.path.join(BASE_DIR, "..", "static", "data", "training_info.json")
        with open(info_file, 'w') as f:
            json.dump(training_info, f, indent=2)
        
        print("\n" + "=" * 60)
        print("Training Complete!")
        print("=" * 60)
        
        return training_info
    
    def retrain_with_learning_data(self, epochs=100):
        """Retrain model incorporating self-learning data"""
        print("\nRetraining with self-learning data...")
        return self.train(epochs=epochs)
    
    def incremental_train(self, new_patterns, epochs=50):
        """Incremental training with new patterns"""
        print("\nIncremental training with new patterns...")
        
        # Load existing model
        if os.path.exists(MODEL_FILE):
            print("Loading existing model...")
            self.model = load_model(MODEL_FILE)
            
            # Load existing data
            with open(DATA_PICKLE, "rb") as f:
                self.training_data = pickle.load(f)
                self.words = self.training_data["words"]
                self.classes = self.training_data["classes"]
        
        # Add new patterns
        for pattern_data in new_patterns:
            pattern = pattern_data.get("pattern", "")
            tag = pattern_data.get("intent", "")
            
            if tag in self.classes:
                words = self.tokenize_and_lemmatize(pattern)
                self.words.extend(words)
                self.documents.append((words, tag))
        
        # Retrain
        return self.train(epochs=epochs)


def train_model(epochs=200, auto=False):
    """
    Main training function
    
    Args:
        epochs: Number of training epochs
        auto: Whether to automatically retrain with learning data
    """
    trainer = ChatbotTrainer()
    
    if auto:
        return trainer.retrain_with_learning_data(epochs)
    else:
        return trainer.train(epochs)


def quick_train():
    """Quick training with fewer epochs for testing"""
    trainer = ChatbotTrainer()
    return trainer.train(epochs=50)


if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        print("Running quick training...")
        quick_train()
    elif len(sys.argv) > 1 and sys.argv[1] == "--auto":
        print("Running auto training with learning data...")
        train_model(epochs=150, auto=True)
    else:
        print("Running full training...")
        train_model(epochs=200)
