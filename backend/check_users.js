const mongoose = require('mongoose');

async function check() {
    await mongoose.connect('mongodb://localhost:27017/railway_auth');
    const userSchema = new mongoose.Schema({
        username: String,
        email: String
    });
    const User = mongoose.model('User', userSchema);
    const users = await User.find({});
    console.log(`Found ${users.length} users:`);
    users.forEach(u => console.log(`- ${u.username} (${u.email})`));
    await mongoose.disconnect();
}

check();
