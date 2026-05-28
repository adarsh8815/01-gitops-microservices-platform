const express = require('express');
const prometheus = require('prom-client');
const winston = require('winston');

const app = express();
app.use(express.json());

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(winston.format.timestamp(), winston.format.json()),
  transports: [new winston.transports.Console()]
});

const register = new prometheus.Registry();
prometheus.collectDefaultMetrics({ register });

const httpRequestDuration = new prometheus.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.1, 0.5, 1, 2, 5],
  registers: [register]
});

const httpRequestTotal = new prometheus.Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status_code'],
  registers: [register]
});

app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    httpRequestDuration.labels(req.method, req.path, res.statusCode).observe(duration);
    httpRequestTotal.labels(req.method, req.path, res.statusCode).inc();
    logger.info({ method: req.method, path: req.path, status: res.statusCode, duration });
  });
  next();
});

const users = new Map();

app.get('/health', (req, res) => res.json({ status: 'healthy', service: 'user-service', version: process.env.APP_VERSION || 'v1.0.0', timestamp: new Date() }));
app.get('/ready', (req, res) => res.json({ status: 'ready' }));
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

app.post('/api/v1/users', (req, res) => {
  const { name, email, role } = req.body;
  if (!name || !email) return res.status(400).json({ error: 'name and email required' });
  const id = `user_${Date.now()}`;
  const user = { id, name, email, role: role || 'user', createdAt: new Date() };
  users.set(id, user);
  logger.info({ event: 'user_created', userId: id });
  res.status(201).json(user);
});

app.get('/api/v1/users', (req, res) => {
  res.json({ users: Array.from(users.values()), total: users.size });
});

app.get('/api/v1/users/:id', (req, res) => {
  const user = users.get(req.params.id);
  if (!user) return res.status(404).json({ error: 'User not found' });
  res.json(user);
});

app.put('/api/v1/users/:id', (req, res) => {
  const user = users.get(req.params.id);
  if (!user) return res.status(404).json({ error: 'User not found' });
  const updated = { ...user, ...req.body, updatedAt: new Date() };
  users.set(req.params.id, updated);
  res.json(updated);
});

app.delete('/api/v1/users/:id', (req, res) => {
  if (!users.has(req.params.id)) return res.status(404).json({ error: 'User not found' });
  users.delete(req.params.id);
  res.status(204).send();
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => logger.info({ event: 'server_started', port: PORT, env: process.env.NODE_ENV }));

module.exports = app;
