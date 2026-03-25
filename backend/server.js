const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const nodemailer = require('nodemailer');
require('dotenv').config();

const app = express();
app.use(express.json());
app.use(cors());

// MongoDB connection
mongoose.connect(process.env.MONGO_URI || 'mongodb://localhost:27017/railway_auth')
    .then(() => console.log('✅ Connected to MongoDB (localhost)'))
    .catch(err => console.error('❌ MongoDB Connection Error:', err));

// User Schema
const userSchema = new mongoose.Schema({
    username: { type: String, required: true, unique: true },
    email: { type: String, required: true, unique: true },
    password: { type: String, required: true }
});

const User = mongoose.model('User', userSchema);

// JWT Middleware
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) return res.sendStatus(401);

    jwt.verify(token, process.env.JWT_SECRET || 'secret_key', (err, user) => {
        if (err) return res.sendStatus(403);
        req.user = user;
        next();
    });
};

// Routes
app.post('/api/auth/register', async (req, res) => {
    try {
        const { username, email, password } = req.body;
        
        // Check if user exists
        const existingUser = await User.findOne({ $or: [{ email }, { username }] });
        if (existingUser) {
            return res.status(400).json({ success: false, message: 'User already exists' });
        }

        // Hash password
        const hashedPassword = await bcrypt.hash(password, 10);
        const newUser = new User({ username, email, password: hashedPassword });
        await newUser.save();

        res.status(201).json({ success: true, message: 'User registered successfully' });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

app.post('/api/auth/login', async (req, res) => {
    try {
        const { email, password } = req.body;
        const user = await User.findOne({ email });
        
        if (!user || !(await bcrypt.compare(password, user.password))) {
            return res.status(401).json({ success: false, message: 'Invalid credentials' });
        }

        const token = jwt.sign(
            { id: user._id, username: user.username },
            process.env.JWT_SECRET || 'secret_key',
            { expiresIn: '24h' }
        );

        res.json({ success: true, token, username: user.username });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

app.get('/api/auth/verify', authenticateToken, (req, res) => {
    res.json({ success: true, user: req.user });
});

// ── Notification Service ──

const transporter = nodemailer.createTransport({
    service: 'gmail', // Or configure based on .env
    auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASS
    }
});

app.post('/api/notify', async (req, res) => {
    try {
        const { train_id, delay, justification, resolved_count, status } = req.body;
        
        // 1. Fetch all officer emails
        const officers = await User.find({}, 'email username');
        const emails = officers.map(o => o.email);

        if (emails.length === 0) {
            console.log('⚠️ No officer emails found for notification.');
            return res.json({ success: true, message: 'No recipients' });
        }

        // 2. Prepare Email
        const mailOptions = {
            from: process.env.EMAIL_USER || 'railway.ai.alert@gmail.com',
            to: emails.join(', '),
            subject: `🚨 Official Alert: Train ${train_id} Rescheduled`,
            text: `
                Railway Intelligence System Alert
                ---------------------------------
                A new rescheduling has been triggered:
                
                - Train ID: ${train_id}
                - New Delay: ${delay} minutes
                - AI Reasoning: ${justification}
                - Conflicts Resolved: ${resolved_count}
                - Pipeline Status: ${status}
                
                Please log in to the dashboard for manual verification if required.
                
                System Timestamp: ${new Date().toISOString()}
            `
        };

        // 3. Send (Logged for tracking)
        console.log(`📧 Dispatching alerts to ${emails.length} officers: ${emails.join(', ')}`);
        
        // Only attempt to send if credentials exist
        if (process.env.EMAIL_USER && process.env.EMAIL_PASS) {
            await transporter.sendMail(mailOptions);
            console.log('✅ Emails sent successfully via Nodemailer.');
        } else {
            console.log('💡 Note: EMAIL_USER/PASS not set; email sending was skipped but logic is ready.');
        }

        res.json({ success: true, recipients: emails.length });
    } catch (err) {
        console.error('❌ Notification Error:', err);
        res.status(500).json({ success: false, message: err.message });
    }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`🚀 Auth Backend running on port ${PORT}`);
});
