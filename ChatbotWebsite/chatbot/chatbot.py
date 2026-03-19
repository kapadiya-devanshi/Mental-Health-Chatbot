import json
import random
import numpy as np
import nltk
import pickle
import re
from autocorrect import Speller
from nltk.stem import WordNetLemmatizer
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import Adam
from keras.models import load_model

nltk.download("punkt")
nltk.download("wordnet")

# Lemmatizer
lemmatizer = WordNetLemmatizer()

# load intents
with open("ChatbotWebsite/static/data/intents.json") as file:
    intents = json.load(file)

# Emotional Intelligence - Sentiment Analysis Patterns
EMOTIONAL_PATTERNS = {
    "anxious": {
        "keywords": ["anxious", "anxiety", "worried", "worry", "panic", "nervous", "stressed", "overwhelmed", "cant breathe", "racing heart", "restless", "on edge", "tense", "fear", "scared", "afraid", "dread"],
        "response_style": "calming",
        "techniques": ["grounding", "breathing", "reassurance"]
    },
    "sad": {
        "keywords": ["sad", "depressed", "depression", "hopeless", "empty", "numb", "crying", "cry", "tears", "lonely", "alone", "isolated", "grief", "loss", "heartbroken", "melancholy", "despair"],
        "response_style": "empathetic",
        "techniques": ["validation", "gentle_support", "hope"]
    },
    "angry": {
        "keywords": ["angry", "anger", "mad", "furious", "rage", "irritated", "annoyed", "frustrated", "hate", "pissed", "resent", "bitter"],
        "response_style": "validating",
        "techniques": ["acknowledgment", "venting_space", "cooling"]
    },
    "happy": {
        "keywords": ["happy", "joy", "excited", "grateful", "blessed", "good", "great", "wonderful", "amazing", "fantastic", "love", "loved", "content", "peaceful"],
        "response_style": "celebratory",
        "techniques": ["encouragement", "reinforcement"]
    },
    "confused": {
        "keywords": ["confused", "lost", "dont understand", "uncertain", "unsure", "dont know", "help me", "guidance", "direction"],
        "response_style": "clarifying",
        "techniques": ["simplification", "step_by_step"]
    }
}

# Evidence-Based Coping Techniques
COPING_TECHNIQUES = {
    "grounding": [
        "Let's try the 5-4-3-2-1 technique: Name 5 things you see, 4 things you can touch, 3 things you hear, 2 things you smell, and 1 thing you taste. Take your time with each one.",
        "Place both feet firmly on the ground. Feel the connection between your feet and the floor. You're here, you're safe, and you're grounded in this moment.",
        "Try holding an ice cube or splashing cold water on your wrists. The cool sensation can help anchor you to the present moment."
    ],
    "breathing": [
        "Let's breathe together: Inhale slowly for 4 counts... hold for 4... exhale for 6. Feel your body relaxing with each breath out.",
        "Place one hand on your chest and one on your belly. Breathe so your belly hand rises more than your chest hand. Slow and steady.",
        "Try box breathing: Inhale for 4, hold for 4, exhale for 4, hold for 4. Repeat this cycle a few times with me."
    ],
    "reassurance": [
        "What you're feeling is valid, and it will pass. You've gotten through difficult moments before, and you will get through this one too.",
        "Remember: feelings are visitors. They come and they go. You are the home they pass through, not the feelings themselves.",
        "This moment is hard, but you don't have to face it alone. I'm right here with you."
    ],
    "validation": [
        "It makes complete sense that you feel this way. Anyone in your situation would likely feel similar emotions.",
        "Your feelings are valid, even if they're painful. You don't need to justify why you feel what you feel.",
        "I hear the weight in your words. What you're carrying sounds really heavy, and I want you to know that your struggle is real."
    ],
    "gentle_support": [
        "Be gentle with yourself today, like you would be with a dear friend going through the same thing.",
        "Small steps count. Getting through today is enough. You don't have to have everything figured out right now.",
        "Your best is enough, even if today's best looks different from yesterday's."
    ],
    "hope": [
        "Even the darkest night will end and the sun will rise. This feeling is temporary, even if it doesn't feel that way right now.",
        "There is hope, even when your mind tells you there isn't. Better moments are ahead, even if we can't see them yet.",
        "You are stronger than you know, and this pain won't last forever. Brighter days are coming."
    ],
    "acknowledgment": [
        "I can hear how frustrated you are. Your anger makes sense given what you're dealing with.",
        "It sounds like something really pushed your buttons. That kind of irritation is completely understandable.",
        "Your feelings of anger are valid. Something important to you has been affected, and that matters."
    ],
    "venting_space": [
        "I'm here to listen. Tell me more about what's bothering you - let it all out.",
        "Sometimes we just need to get it out. I'm a safe space for you to express whatever you need to say.",
        "Go ahead, I'm listening. What else is on your mind about this?"
    ],
    "cooling": [
        "When you're ready, we could try taking a few deep breaths together. No rush - just when you feel like it.",
        "Sometimes a change of scenery helps - even just stepping outside for a moment or looking out a window.",
        "Your body might appreciate some movement right now - a walk, some stretching, or even just shaking out your limbs."
    ],
    "encouragement": [
        "I'm so glad you're feeling this way! You deserve these moments of joy.",
        "What a beautiful feeling! Hold onto this moment and let it warm you.",
        "Your happiness shines through your words. This is wonderful to hear!"
    ],
    "reinforcement": [
        "These positive moments are building blocks. You're creating a foundation of goodness for yourself.",
        "Celebrate this feeling - you've cultivated it, and that's something to be proud of.",
        "This joy you're experiencing? You absolutely deserve it. Let yourself fully feel it."
    ],
    "simplification": [
        "Let's break this down into smaller pieces. What's the one thing that feels most important right now?",
        "Sometimes things feel clearer when we look at just one step at a time. What would help most in this moment?",
        "You don't need to solve everything right now. Let's focus on what feels manageable first."
    ],
    "step_by_step": [
        "Let's take this one step at a time together. First, tell me what feels most urgent to address.",
        "We can work through this together, piece by piece. Where would you like to start?",
        "Small steps lead to big changes. What's one tiny thing you could do right now that might help?"
    ]
}

# Human-centric response templates (no canned AI phrases)
HUMAN_CENTRIC_OPENERS = {
    "anxious": [
        "I can hear the worry in your words...",
        "It sounds like your mind is racing right now...",
        "I notice you might be feeling on edge...",
        "That tight, anxious feeling you're describing..."
    ],
    "sad": [
        "My heart goes out to you as I read this...",
        "I can feel the heaviness in what you're sharing...",
        "It sounds like you're carrying a lot right now...",
        "The pain you're describing is so real..."
    ],
    "angry": [
        "I can sense the frustration coming through...",
        "That sounds incredibly irritating...",
        "I hear you - something really pushed your buttons...",
        "The anger you're feeling is completely understandable..."
    ],
    "happy": [
        "This is wonderful to hear!",
        "Your joy is coming through loud and clear!",
        "I'm smiling reading this!",
        "What a beautiful moment you're sharing!"
    ],
    "neutral": [
        "I'm listening...",
        "Tell me more about that...",
        "I hear you...",
        "I'm here with you..."
    ]
}

# Language detection for linguistic mirroring
LANGUAGE_PATTERNS = {
    "formal": ["would", "could", "shall", "may", "indeed", "furthermore", "however", "therefore"],
    "casual": ["gonna", "wanna", "kinda", "sorta", "yeah", "nah", "lol", "haha", "omg", "tbh"],
    "slang": ["dope", "lit", "vibes", "lowkey", "highkey", "bet", "fam", "sus", "cap", "no cap"]
}

try:  # load saved model if existed
    with open("data.pickle", "rb") as f:
        words, classes, training, output = pickle.load(f)
    model = load_model("chatbot-model.h5")
except:  # create new model if not existed
    # create list of words, tags, and tuples (pattern+tag), and ignore words
    words = []
    classes = []
    documents = []
    ignore_words = ["?", "!", ".", ","]

    # loop through intents and patterns
    for intent in intents["intents"]:
        for pattern in intent["patterns"]:
            word_list = nltk.word_tokenize(pattern)  # tokenize each word
            words.extend(word_list)  # add to words list
            # add to patterns list
            documents.append(((word_list), intent["tag"]))

            if intent["tag"] not in classes:  # add to tags list if not already there
                classes.append(intent["tag"])

    words = [
        lemmatizer.lemmatize(word.lower()) for word in words if word not in ignore_words
    ]  # lemmatize and lower each word
    # remove duplicates and sort
    words = sorted(set(words))
    classes = sorted(set(classes))

    # create training data
    training = []
    output = []
    out_empty = [0] * len(classes)  # empty list for output

    for document in documents:
        bag = []
        word_patterns = document[0]
        word_patterns = [
            lemmatizer.lemmatize(w.lower()) for w in word_patterns
        ]  # lemmatize each word

        for word in words:
            bag.append(1) if word in word_patterns else bag.append(0)
        output_row = list(out_empty)
        output_row[classes.index(document[1])] = 1
        training.append(bag)
        output.append(output_row)

    training = np.array(training)
    output = np.array(output)

    with open("data.pickle", "wb") as f:
        pickle.dump((words, classes, training, output), f)

    # create model (machine learning)
    model = Sequential()
    model.add(
        Dense(256, input_shape=(len(training[0]),), activation="relu")
    )  # input layer
    model.add(Dropout(0.4))  # dropout layer
    model.add(Dense(128, activation="relu"))  # hidden layer
    model.add(Dropout(0.4))  # dropout layer
    model.add(Dense(64, activation="relu"))  # hidden layer
    model.add(Dropout(0.4))  # dropout layer
    model.add(Dense(len(output[0]), activation="softmax"))  # output layer
    adam = Adam(learning_rate=0.001)  # optimizer
    model.compile(
        loss="categorical_crossentropy", optimizer=adam, metrics=["accuracy"]
    )  # compile model
    model.fit(
        training, output, epochs=300, batch_size=10, verbose=1
    )  # fit model (train)
    model.save("chatbot-model.h5")  # save model
    print("Done")


# clean up message
def clean_up_message(message):
    message_word_list = nltk.word_tokenize(message)
    message_word_list = [
        lemmatizer.lemmatize(word.lower()) for word in message_word_list
    ]
    return message_word_list


# bag of words, 0 or 1 for each word in the bag that exists in the message
def bag_of_words(message, words):
    message_word = clean_up_message(message)
    bag = [0] * len(words)
    for w in message_word:
        for i, word in enumerate(words):
            if word == w:
                bag[i] = 1
    return np.array(bag)


# context
context = {}

# Crisis keywords for safety detection
CRISIS_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "end my life", "want to die",
    "self-harm", "self harm", "cutting myself", "hurt myself", "harm myself",
    "not worth living", "better off dead", "can't go on", "no reason to live",
    "violence", "hurt someone", "kill someone", "harm others", "attack"
]

# Medical advice keywords
MEDICAL_KEYWORDS = [
    "diagnose", "diagnosis", "prescribe", "medication", "drug", "treatment",
    "cure", "heal", "fix my", "what's wrong with me", "mental illness",
    "disorder", "condition", "therapy", "therapist", "psychiatrist",
    "psychologist", "doctor", "physician", "medical advice"
]


def check_safety_flag(message):
    """Check if message contains crisis/self-harm indicators."""
    message_lower = message.lower()
    for keyword in CRISIS_KEYWORDS:
        if keyword in message_lower:
            return True
    return False


def check_medical_disclaimer(message):
    """Check if message requests medical advice."""
    message_lower = message.lower()
    for keyword in MEDICAL_KEYWORDS:
        if keyword in message_lower:
            return True
    return False


# predict class, return list of tuples (tag, probability)
def predict_class(message, ERROR_THRESHOLD=0.25):
    bow = bag_of_words(message, words)
    res = model.predict(np.array([bow]))[0]
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append((classes[r[0]], r[1]))
    return return_list


# get response, return structured JSON response
def get_response(message, id="000"):
    spell = Speller()  # autocorrect
    corrected_message = spell(message)
    
    # Initialize response structure
    response_data = {
        "response": "",
        "safety_flag": False,
        "medical_disclaimer": False,
        "crisis_resources": None,
        "emotional_state": "neutral",
        "language_style": "neutral",
        "intent_tag": "unknown"
    }
    
    # Check for safety concerns
    if check_safety_flag(corrected_message):
        response_data["safety_flag"] = True
        response_data["response"] = "I'm really concerned about what you've shared. Your safety matters more than anything right now. Please reach out to a crisis helpline immediately - there are caring people waiting to help:\n\n• Call or text 988 (Suicide & Crisis Lifeline)\n• Text HOME to 741741 (Crisis Text Line)\n• Call 911 if you're in immediate danger\n\nYou are not alone in this. These feelings are temporary, even when they feel permanent. Please reach out - you matter."
        response_data["crisis_resources"] = [
            {"name": "988 Suicide & Crisis Lifeline", "contact": "Call or text 988"},
            {"name": "Crisis Text Line", "contact": "Text HOME to 741741"},
            {"name": "Emergency Services", "contact": "Call 911"}
        ]
        return response_data
    
    # Emotional Intelligence: Detect emotional state and language style
    emotional_state = detect_emotional_state(corrected_message)
    language_style = detect_language_style(corrected_message)
    
    response_data["emotional_state"] = emotional_state
    response_data["language_style"] = language_style
    
    # Check for medical advice request
    needs_medical_disclaimer = check_medical_disclaimer(corrected_message)
    
    results = predict_class(corrected_message)  # get list of tuples (tag, probability)
    
    if results:  # if results exist
        while results:  # loop through results
            for intent in intents["intents"]:  # loop through intents
                if intent["tag"] == results[0][0]:  # if tag matches
                    if intent["tag"].lower() == "reiterate":  # if tag is reiterate
                        if context:  # if context exists
                            for tg in intents["intents"]:
                                if (
                                    "context_set" in tg
                                    and tg["context_set"] == context[id]
                                ):
                                    response_text = random.choice(tg["responses"])
                                    # Apply emotional intelligence
                                    response_text = enhance_response_with_emotional_intelligence(
                                        corrected_message, response_text, emotional_state
                                    )
                                    # Apply linguistic mirroring
                                    response_text = adapt_response_style(response_text, language_style)
                                    response_data["response"] = response_text
                                    response_data["medical_disclaimer"] = needs_medical_disclaimer
                                    return response_data
                        else:
                            response_text = random.choice(intent["responses"])
                            response_text = enhance_response_with_emotional_intelligence(
                                corrected_message, response_text, emotional_state
                            )
                            response_text = adapt_response_style(response_text, language_style)
                            response_data["response"] = response_text
                            response_data["medical_disclaimer"] = needs_medical_disclaimer
                            return response_data
                    if "context_set" in intent and intent["context_set"] != "":
                        context[id] = intent["context_set"]
                    response_text = random.choice(intent["responses"])
                    # Apply emotional intelligence to enhance the response
                    response_text = enhance_response_with_emotional_intelligence(
                        corrected_message, response_text, emotional_state
                    )
                    # Apply linguistic mirroring
                    response_text = adapt_response_style(response_text, language_style)
                    response_data["response"] = response_text
                    response_data["medical_disclaimer"] = needs_medical_disclaimer
                    response_data["intent_tag"] = intent["tag"]
                    return response_data
            results.pop(0)
    else:  # if no results - provide emotionally intelligent fallback
        # Create a warm, human-centric fallback response
        if emotional_state == "anxious":
            response_text = "I can hear there's something on your mind, even if I'm not quite sure what it is. That's okay - you don't have to have all the words right now. I'm here to listen whenever you're ready to share more."
        elif emotional_state == "sad":
            response_text = "I sense there might be something heavy you're carrying right now. You don't have to go through it alone. I'm here to sit with you in this moment, whatever you're feeling."
        elif emotional_state == "angry":
            response_text = "Something's clearly bothering you, and that's completely valid. Sometimes things just feel frustrating, and you don't need to explain why. I'm here if you want to talk about it."
        elif emotional_state == "confused":
            response_text = "It sounds like things might feel a bit unclear right now. That's completely okay - we all have moments like that. Would you like to try talking through it together?"
        else:
            response_text = "I'm here with you, ready to listen. Whether you want to talk about something specific or just need a supportive presence, I'm here for you. What would feel helpful right now?"
        
        response_text = adapt_response_style(response_text, language_style)
        response_data["response"] = response_text
        response_data["medical_disclaimer"] = needs_medical_disclaimer
    
    return response_data


# Emotional Intelligence Functions
def detect_emotional_state(message):
    """Analyze the user's message to detect emotional state."""
    message_lower = message.lower()
    emotion_scores = {}
    
    for emotion, data in EMOTIONAL_PATTERNS.items():
        score = 0
        for keyword in data["keywords"]:
            if keyword in message_lower:
                score += 1
        if score > 0:
            emotion_scores[emotion] = score
    
    if emotion_scores:
        return max(emotion_scores, key=emotion_scores.get)
    return "neutral"


def detect_language_style(message):
    """Detect the formality level of user's message for linguistic mirroring."""
    message_lower = message.lower()
    
    slang_count = sum(1 for word in LANGUAGE_PATTERNS["slang"] if word in message_lower)
    casual_count = sum(1 for word in LANGUAGE_PATTERNS["casual"] if word in message_lower)
    formal_count = sum(1 for word in LANGUAGE_PATTERNS["formal"] if word in message_lower)
    
    # Check for contractions (casual indicator)
    contraction_count = len(re.findall(r"\w+'\w+", message))
    
    if slang_count > 0:
        return "slang"
    elif casual_count > 0 or contraction_count > 2:
        return "casual"
    elif formal_count > 0:
        return "formal"
    return "neutral"


def get_emotional_response(emotion, technique=None):
    """Generate an emotionally intelligent response based on detected emotion."""
    opener = random.choice(HUMAN_CENTRIC_OPENERS.get(emotion, HUMAN_CENTRIC_OPENERS["neutral"]))
    
    if emotion in EMOTIONAL_PATTERNS and technique:
        techniques = EMOTIONAL_PATTERNS[emotion]["techniques"]
        if technique in techniques:
            technique_response = random.choice(COPING_TECHNIQUES[technique])
            return f"{opener}\n\n{technique_response}"
    
    return opener


def adapt_response_style(response, language_style):
    """Adapt response to match user's language style (linguistic mirroring)."""
    if language_style == "slang":
        # Make it more casual and relatable
        response = response.replace("I am", "I'm").replace("you are", "you're")
        response = response.replace("do not", "don't").replace("cannot", "can't")
    elif language_style == "casual":
        # Keep it friendly but not overly formal
        response = response.replace("I am", "I'm").replace("you are", "you're")
        response = response.replace("do not", "don't").replace("cannot", "can't")
    elif language_style == "formal":
        # Keep it more structured
        pass
    
    return response


def enhance_response_with_emotional_intelligence(message, base_response, emotion):
    """Enhance base response with emotional intelligence based on detected emotion."""
    if emotion == "anxious":
        # For anxiety: calming, short sentences, grounding techniques
        opener = random.choice(HUMAN_CENTRIC_OPENERS["anxious"])
        technique = random.choice(["grounding", "breathing", "reassurance"])
        technique_response = random.choice(COPING_TECHNIQUES[technique])
        
        # Keep sentences shorter for anxious users
        enhanced = f"{opener}\n\n{technique_response}\n\n{base_response}"
        return enhanced
    
    elif emotion == "sad":
        # For sadness: deep validation, gentle support, hope
        opener = random.choice(HUMAN_CENTRIC_OPENERS["sad"])
        technique = random.choice(["validation", "gentle_support", "hope"])
        technique_response = random.choice(COPING_TECHNIQUES[technique])
        
        enhanced = f"{opener}\n\n{technique_response}\n\n{base_response}"
        return enhanced
    
    elif emotion == "angry":
        # For anger: validation, space to vent, cooling techniques
        opener = random.choice(HUMAN_CENTRIC_OPENERS["angry"])
        technique = random.choice(["acknowledgment", "venting_space", "cooling"])
        technique_response = random.choice(COPING_TECHNIQUES[technique])
        
        enhanced = f"{opener}\n\n{technique_response}\n\n{base_response}"
        return enhanced
    
    elif emotion == "happy":
        # For happiness: celebration, reinforcement
        opener = random.choice(HUMAN_CENTRIC_OPENERS["happy"])
        technique = random.choice(["encouragement", "reinforcement"])
        technique_response = random.choice(COPING_TECHNIQUES[technique])
        
        enhanced = f"{opener}\n\n{technique_response}\n\n{base_response}"
        return enhanced
    
    elif emotion == "confused":
        # For confusion: simplification, step-by-step
        opener = random.choice(HUMAN_CENTRIC_OPENERS["neutral"])
        technique = random.choice(["simplification", "step_by_step"])
        technique_response = random.choice(COPING_TECHNIQUES[technique])
        
        enhanced = f"{opener}\n\n{technique_response}\n\n{base_response}"
        return enhanced
    
    return base_response


# Legacy function for backward compatibility - returns just the text response
def get_response_text(message, id="000"):
    """Get response as plain text for backward compatibility."""
    response_data = get_response(message, id)
    return response_data["response"]
