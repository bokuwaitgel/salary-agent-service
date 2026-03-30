module.exports = {
  apps: [
    {
      name: "salary-api",
      script: "run_api.py",
      interpreter: "python",
      cwd: __dirname,
      env: {
        API_HOST: "0.0.0.0",
        API_PORT: "8007",
        API_WORKERS: "1",
        API_LOG_LEVEL: "info",
      },
      watch: false,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
    },
    {
      name: "salary-dashboard",
      script: "run_dashboard.py",
      interpreter: "python",
      cwd: __dirname,
      env: {
        DASH_HOST: "0.0.0.0",
        DASH_PORT: "8006",
        DASH_THREADS: "4",
      },
      watch: false,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
    },
  ],
};
