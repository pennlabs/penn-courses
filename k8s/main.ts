import { Construct } from 'constructs';
import { App } from 'cdk8s';
import { CronJob, DjangoApplication, PennLabsChart, ReactApplication, RedisApplication } from '@pennlabs/kittyhawk';

const cronTime = require('cron-time-generator');

export class MyChart extends PennLabsChart {
  constructor(scope: Construct) {
    super(scope);

    const backendImage = 'pennlabs/penn-courses-backend';
    const secret = 'penn-courses';

    new RedisApplication(this, 'redis', { deployment: { tag: '4.0' } });

    new DjangoApplication(this, 'celery', {
      deployment: {
        image: backendImage,
        secret,
        cmd: ['celery', 'worker', '-A', 'PennCourses', '-Q', 'alerts,celery', '-linfo'],
      },
      djangoSettingsModule: 'PennCourses.settings.production',
    });

    new DjangoApplication(this, 'backend', {
      deployment: {
        image: backendImage,
        secret,
        replicas: 3,
      },
      djangoSettingsModule: 'PennCourses.settings.production',
      ingressProps: {
        annotations: { ['ingress.kubernetes.io/content-security-policy']: "frame-ancestors 'none';" },
      },
      domains: [{ host: 'penncourseplan.com', paths: ["/api", "/admin", "/accounts", "/assets"] },
      { host: 'penncoursealert.com', paths: ["/api", "/admin", "/accounts", "/assets", "/webhook"] },
      { host: 'penncoursereview.com', paths: ["/api", "/admin", "/accounts", "/assets"] }],
    });

    new ReactApplication(this, 'landing', {
      deployment: {
        image: 'pennlabs/pcx-landing',
      },
      domain: { host: 'penncourses.org', paths: ['/'] },
    });

    new ReactApplication(this, 'plan', {
      deployment: {
        image: 'pennlabs/pcp-frontend',
      },
      domain: { host: 'penncourseplan.com', paths: ['/'] },
    });

    new ReactApplication(this, 'alert', {
      deployment: {
        image: 'pennlabs/pca-frontend',
      },
      domain: { host: 'penncoursealert.com', paths: ['/'] },
    });

    new ReactApplication(this, 'review', {
      deployment: {
        image: 'pennlabs/pcr-frontend',
      },
      domain: { host: 'penncoursereview.com', paths: ['/'] },
    });

    new CronJob(this, 'load-courses', {
      schedule: cronTime.everyDayAt(3),
      image: backendImage,
      secret,
      cmd: ['python', 'manage.py', 'registrarimport'],
    });

    new CronJob(this, 'report-stats', {
      schedule: cronTime.everyDayAt(20),
      image: backendImage,
      secret,
      cmd: ['python', 'manage.py', 'alertstats', '1', '--slack'],
    });

  }
}

const app = new App();
new MyChart(app);
app.synth();
