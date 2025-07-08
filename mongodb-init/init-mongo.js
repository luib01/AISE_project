// MongoDB initialization script
// This script runs when the MongoDB container starts for the first time

db = db.getSiblingDB('EnglishLearning');

// Create collections
db.createCollection('Users');
db.createCollection('Quizzes');
db.createCollection('Recommendations');

// Create indexes for better performance
db.Users.createIndex({ "user_id": 1 }, { unique: true });
db.Quizzes.createIndex({ "user_id": 1 });
db.Quizzes.createIndex({ "timestamp": -1 });
db.Recommendations.createIndex({ "user_id": 1 });
db.Recommendations.createIndex({ "timestamp": -1 });

// Insert sample data for testing
db.Users.insertOne({
    user_id: "demo_user",
    english_level: "beginner",
    progress: {
        "Grammar": 75,
        "Vocabulary": 60,
        "Reading": 80
    },
    total_quizzes: 5,
    average_score: 72.0,
    created_at: new Date(),
    last_quiz_date: new Date()
});

print("MongoDB initialized successfully for English Learning Platform!");
print("Created collections: Users, Quizzes, Recommendations");
print("Created indexes for performance optimization");
print("Inserted sample demo user");
