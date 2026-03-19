"""
Self-Learning Module for SoulMate Chatbot
Analyzes user chats and intents.json to continuously improve the AI model
"""

import json
import pickle
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Set
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import os

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# File paths
INTENTS_FILE = "ChatbotWebsite/static/data/intents.json"
LEARNING_DATA_FILE = "ChatbotWebsite/static/data/learning_data.json"
MODEL_FEEDBACK_FILE = "ChatbotWebsite/static/data/model_feedback.pkl"


class SelfLearningEngine:
    """
    Self-learning engine that analyzes user interactions and improves the chatbot
    """
    
    def __init__(self):
        self.intents = self._load_intents()
        self.learning_data = self._load_learning_data()
        self.lemmatizer = WordNetLemmatizer()
        self.confidence_threshold = 0.6
        
    def _load_intents(self) -> Dict:
        """Load intents from JSON file"""
        try:
            with open(INTENTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading intents: {e}")
            return {"intents": []}
    
    def _load_learning_data(self) -> Dict:
        """Load learning data from file"""
        try:
            with open(LEARNING_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Initialize learning data structure
            return {
                "user_patterns": {},  # user_input -> {intent_tag, frequency, last_used}
                "failed_queries": [],  # Queries that didn't match well
                "new_patterns": {},    # New patterns discovered from chats
                "intent_stats": {},    # Statistics per intent
                "response_feedback": {},  # response -> {positive, negative}
                "last_updated": datetime.now().isoformat()
            }
    
    def _save_learning_data(self):
        """Save learning data to file"""
        try:
            self.learning_data["last_updated"] = datetime.now().isoformat()
            with open(LEARNING_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.learning_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving learning data: {e}")
    
    def _save_intents(self):
        """Save updated intents to file"""
        try:
            with open(INTENTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.intents, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving intents: {e}")
    
    def tokenize_and_lemmatize(self, text: str) -> List[str]:
        """Tokenize and lemmatize text"""
        # Clean text
        text = re.sub(r'[^\w\s]', '', text.lower())
        # Tokenize
        tokens = nltk.word_tokenize(text)
        # Lemmatize
        return [self.lemmatizer.lemmatize(token) for token in tokens]
    
    def analyze_intents(self) -> Dict:
        """Analyze intents.json and return statistics"""
        stats = {
            "total_intents": len(self.intents.get("intents", [])),
            "total_patterns": 0,
            "total_responses": 0,
            "patterns_per_intent": {},
            "responses_per_intent": {},
            "all_keywords": set()
        }
        
        for intent in self.intents.get("intents", []):
            tag = intent.get("tag", "unknown")
            patterns = intent.get("patterns", [])
            responses = intent.get("responses", [])
            
            stats["total_patterns"] += len(patterns)
            stats["total_responses"] += len(responses)
            stats["patterns_per_intent"][tag] = len(patterns)
            stats["responses_per_intent"][tag] = len(responses)
            
            # Extract keywords
            for pattern in patterns:
                words = self.tokenize_and_lemmatize(pattern)
                stats["all_keywords"].update(words)
        
        stats["unique_keywords"] = len(stats["all_keywords"])
        return stats
    
    def analyze_user_chats(self, chat_messages: List[Dict]) -> Dict:
        """Analyze user chat history to extract insights"""
        analysis = {
            "total_interactions": 0,
            "user_messages": [],
            "bot_responses": [],
            "conversation_pairs": [],
            "common_phrases": Counter(),
            "unmatched_queries": [],
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0}
        }
        
        # Sentiment keywords
        positive_words = {'happy', 'good', 'great', 'amazing', 'love', 'thanks', 'thank', 'better', 'well', 'good'}
        negative_words = {'sad', 'bad', 'terrible', 'hate', 'worried', 'anxious', 'depressed', 'lonely', 'stressed'}
        
        prev_message = None
        for msg in chat_messages:
            if msg.get("sender") == "user":
                user_text = msg.get("message", "").strip()
                if user_text:
                    analysis["user_messages"].append(user_text)
                    analysis["total_interactions"] += 1
                    
                    # Analyze sentiment
                    words = set(self.tokenize_and_lemmatize(user_text))
                    if words & positive_words:
                        analysis["sentiment_distribution"]["positive"] += 1
                    elif words & negative_words:
                        analysis["sentiment_distribution"]["negative"] += 1
                    else:
                        analysis["sentiment_distribution"]["neutral"] += 1
                    
                    # Store for conversation pair
                    prev_message = user_text
                    
            elif msg.get("sender") == "bot" and prev_message:
                bot_text = msg.get("message", "").strip()
                if bot_text:
                    analysis["bot_responses"].append(bot_text)
                    analysis["conversation_pairs"].append({
                        "user": prev_message,
                        "bot": bot_text,
                        "timestamp": msg.get("timestamp")
                    })
                    prev_message = None
        
        # Find common phrases (3-grams)
        for msg in analysis["user_messages"]:
            words = self.tokenize_and_lemmatize(msg)
            for i in range(len(words) - 2):
                phrase = ' '.join(words[i:i+3])
                analysis["common_phrases"][phrase] += 1
        
        return analysis
    
    def find_similar_patterns(self, new_pattern: str, threshold: float = 0.7) -> List[Tuple[str, float]]:
        """Find similar existing patterns using TF-IDF similarity"""
        all_patterns = []
        pattern_to_intent = {}
        
        for intent in self.intents.get("intents", []):
            tag = intent.get("tag", "")
            for pattern in intent.get("patterns", []):
                all_patterns.append(pattern)
                pattern_to_intent[pattern] = tag
        
        if not all_patterns:
            return []
        
        # Add new pattern for comparison
        all_patterns.append(new_pattern)
        
        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(
            tokenizer=self.tokenize_and_lemmatize,
            lowercase=True,
            stop_words='english'
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(all_patterns)
            
            # Calculate cosine similarity
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
            
            # Find matches above threshold
            matches = []
            for i, sim in enumerate(similarities):
                if sim >= threshold:
                    matches.append((all_patterns[i], sim, pattern_to_intent.get(all_patterns[i], "")))
            
            # Sort by similarity
            matches.sort(key=lambda x: x[1], reverse=True)
            return [(m[0], m[1]) for m in matches[:5]]  # Return top 5
            
        except Exception as e:
            print(f"Error in similarity calculation: {e}")
            return []
    
    def suggest_intent_for_pattern(self, pattern: str) -> List[Tuple[str, float]]:
        """Suggest which intent a new pattern might belong to"""
        similar = self.find_similar_patterns(pattern, threshold=0.5)
        
        # Count matches per intent
        intent_scores = defaultdict(float)
        for matched_pattern, similarity in similar:
            for intent in self.intents.get("intents", []):
                if matched_pattern in intent.get("patterns", []):
                    intent_scores[intent["tag"]] += similarity
        
        # Sort by score
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_intents[:3]  # Return top 3 suggestions
    
    def extract_new_patterns(self, chat_analysis: Dict, min_frequency: int = 2) -> List[Dict]:
        """Extract new patterns from user chats that could be added to intents"""
        new_patterns = []
        
        # Get common phrases that appear multiple times
        for phrase, count in chat_analysis["common_phrases"].items():
            if count >= min_frequency:
                # Check if this pattern already exists
                similar = self.find_similar_patterns(phrase, threshold=0.8)
                
                if not similar:  # If no similar pattern exists
                    # Suggest intent
                    suggestions = self.suggest_intent_for_pattern(phrase)
                    
                    new_patterns.append({
                        "pattern": phrase,
                        "frequency": count,
                        "suggested_intents": suggestions,
                        "confidence": suggestions[0][1] if suggestions else 0
                    })
        
        # Also check conversation pairs for new intents
        conversation_clusters = self._cluster_conversations(chat_analysis["conversation_pairs"])
        
        return sorted(new_patterns, key=lambda x: x["frequency"], reverse=True)
    
    def _cluster_conversations(self, conversation_pairs: List[Dict]) -> Dict:
        """Cluster conversation pairs to find potential new intents"""
        if len(conversation_pairs) < 5:
            return {}
        
        # Extract user messages
        user_messages = [pair["user"] for pair in conversation_pairs if pair.get("user")]
        
        if len(user_messages) < 5:
            return {}
        
        # Vectorize messages
        vectorizer = TfidfVectorizer(
            tokenizer=self.tokenize_and_lemmatize,
            lowercase=True,
            max_features=100
        )
        
        try:
            X = vectorizer.fit_transform(user_messages)
            
            # Cluster using DBSCAN
            clustering = DBSCAN(eps=0.5, min_samples=2, metric='cosine')
            labels = clustering.fit_predict(X)
            
            # Group by cluster
            clusters = defaultdict(list)
            for i, label in enumerate(labels):
                if label != -1:  # Ignore noise
                    clusters[label].append(conversation_pairs[i])
            
            return dict(clusters)
            
        except Exception as e:
            print(f"Error in clustering: {e}")
            return {}
    
    def generate_new_responses(self, intent_tag: str, chat_analysis: Dict) -> List[str]:
        """Generate new response variations based on successful conversations"""
        new_responses = []
        
        # Find conversations related to this intent
        for pair in chat_analysis.get("conversation_pairs", []):
            user_msg = pair.get("user", "").lower()
            bot_msg = pair.get("bot", "")
            
            # Check if this conversation relates to the intent
            for intent in self.intents.get("intents", []):
                if intent["tag"] == intent_tag:
                    for pattern in intent.get("patterns", []):
                        if pattern.lower() in user_msg or user_msg in pattern.lower():
                            # This bot response was successful
                            if bot_msg and bot_msg not in intent.get("responses", []):
                                new_responses.append(bot_msg)
        
        return list(set(new_responses))[:5]  # Return unique responses, max 5
    
    def update_intents_with_learning(self, chat_analysis: Dict, approval_required: bool = True) -> Dict:
        """Update intents.json with learned patterns and responses"""
        updates = {
            "new_patterns_added": [],
            "new_responses_added": [],
            "suggestions": [],
            "requires_approval": approval_required
        }
        
        # Extract new patterns
        new_patterns = self.extract_new_patterns(chat_analysis, min_frequency=2)
        
        for pattern_data in new_patterns:
            pattern = pattern_data["pattern"]
            suggestions = pattern_data["suggested_intents"]
            
            if suggestions and suggestions[0][1] >= self.confidence_threshold:
                # High confidence match - suggest adding
                intent_tag = suggestions[0][0]
                
                if approval_required:
                    updates["suggestions"].append({
                        "type": "add_pattern",
                        "pattern": pattern,
                        "intent": intent_tag,
                        "confidence": suggestions[0][1],
                        "frequency": pattern_data["frequency"]
                    })
                else:
                    # Auto-add
                    self._add_pattern_to_intent(intent_tag, pattern)
                    updates["new_patterns_added"].append({
                        "pattern": pattern,
                        "intent": intent_tag
                    })
        
        # Generate new responses
        for intent in self.intents.get("intents", []):
            tag = intent.get("tag", "")
            new_responses = self.generate_new_responses(tag, chat_analysis)
            
            for response in new_responses:
                if approval_required:
                    updates["suggestions"].append({
                        "type": "add_response",
                        "response": response,
                        "intent": tag
                    })
                else:
                    self._add_response_to_intent(tag, response)
                    updates["new_responses_added"].append({
                        "response": response,
                        "intent": tag
                    })
        
        # Save if auto-approved
        if not approval_required:
            self._save_intents()
        
        return updates
    
    def _add_pattern_to_intent(self, intent_tag: str, pattern: str):
        """Add a new pattern to an existing intent"""
        for intent in self.intents.get("intents", []):
            if intent["tag"] == intent_tag:
                if pattern not in intent.get("patterns", []):
                    intent["patterns"].append(pattern)
                    return True
        return False
    
    def _add_response_to_intent(self, intent_tag: str, response: str):
        """Add a new response to an existing intent"""
        for intent in self.intents.get("intents", []):
            if intent["tag"] == intent_tag:
                if response not in intent.get("responses", []):
                    intent["responses"].append(response)
                    return True
        return False
    
    def record_user_feedback(self, user_message: str, bot_response: str, feedback: str, intent_tag: str = None):
        """Record user feedback on bot responses"""
        feedback_key = f"{user_message}|{bot_response}"
        
        if feedback_key not in self.learning_data["response_feedback"]:
            self.learning_data["response_feedback"][feedback_key] = {
                "user_message": user_message,
                "bot_response": bot_response,
                "intent_tag": intent_tag,
                "positive": 0,
                "negative": 0,
                "timestamps": []
            }
        
        self.learning_data["response_feedback"][feedback_key][feedback] += 1
        self.learning_data["response_feedback"][feedback_key]["timestamps"].append(
            datetime.now().isoformat()
        )
        
        self._save_learning_data()
    
    def get_learning_report(self) -> Dict:
        """Generate a comprehensive learning report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "intents_analysis": self.analyze_intents(),
            "learning_stats": {
                "total_user_patterns": len(self.learning_data.get("user_patterns", {})),
                "total_failed_queries": len(self.learning_data.get("failed_queries", [])),
                "total_new_patterns": len(self.learning_data.get("new_patterns", {})),
                "total_response_feedback": len(self.learning_data.get("response_feedback", {}))
            },
            "pending_suggestions": self.learning_data.get("pending_suggestions", [])
        }
        
        return report
    
    def train_from_chats(self, chat_messages: List[Dict], auto_update: bool = False) -> Dict:
        """Main training function - analyze chats and update model"""
        print("Starting self-learning analysis...")
        
        # Analyze user chats
        chat_analysis = self.analyze_user_chats(chat_messages)
        
        # Update intents with learning
        updates = self.update_intents_with_learning(chat_analysis, approval_required=not auto_update)
        
        # Save learning data
        self._save_learning_data()
        
        # Generate report
        report = self.get_learning_report()
        report["latest_updates"] = updates
        report["chat_analysis"] = {
            "total_interactions": chat_analysis["total_interactions"],
            "sentiment_distribution": chat_analysis["sentiment_distribution"],
            "top_common_phrases": chat_analysis["common_phrases"].most_common(10)
        }
        
        print("Self-learning analysis complete!")
        return report


# Global instance
learning_engine = SelfLearningEngine()


def analyze_and_learn(chat_messages: List[Dict] = None, auto_update: bool = False) -> Dict:
    """
    Main entry point for self-learning
    
    Args:
        chat_messages: List of chat message dictionaries
        auto_update: Whether to automatically update intents without approval
    
    Returns:
        Learning report dictionary
    """
    if chat_messages is None:
        # Try to load from database
        try:
            from ChatbotWebsite import create_app
            from ChatbotWebsite.models import ChatMessage
            
            app = create_app()
            with app.app_context():
                messages = ChatMessage.query.all()
                chat_messages = [
                    {
                        "sender": msg.sender,
                        "message": msg.message,
                        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                        "user_id": msg.user_id
                    }
                    for msg in messages
                ]
        except Exception as e:
            print(f"Error loading messages from database: {e}")
            chat_messages = []
    
    return learning_engine.train_from_chats(chat_messages, auto_update)


def get_intent_suggestions(new_pattern: str) -> List[Tuple[str, float]]:
    """Get intent suggestions for a new pattern"""
    return learning_engine.suggest_intent_for_pattern(new_pattern)


def add_pattern_with_approval(intent_tag: str, pattern: str) -> bool:
    """Add a pattern to an intent after approval"""
    success = learning_engine._add_pattern_to_intent(intent_tag, pattern)
    if success:
        learning_engine._save_intents()
    return success


def add_response_with_approval(intent_tag: str, response: str) -> bool:
    """Add a response to an intent after approval"""
    success = learning_engine._add_response_to_intent(intent_tag, response)
    if success:
        learning_engine._save_intents()
    return success


def get_learning_stats() -> Dict:
    """Get current learning statistics"""
    return learning_engine.get_learning_report()


if __name__ == "__main__":
    # Test the self-learning engine
    print("Testing Self-Learning Engine...")
    
    # Analyze intents
    stats = learning_engine.analyze_intents()
    print(f"\nIntents Analysis:")
    print(f"Total intents: {stats['total_intents']}")
    print(f"Total patterns: {stats['total_patterns']}")
    print(f"Total responses: {stats['total_responses']}")
    print(f"Unique keywords: {stats['unique_keywords']}")
    
    print("\nSelf-Learning Engine ready!")
