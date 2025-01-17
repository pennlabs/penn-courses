import { Construct } from 'constructs'
import { App } from 'cdk8s'
import {
	CronJob,
	DjangoApplication,
	PennLabsChart,
	ReactApplication,
	RedisApplication,
} from '@pennlabs/kittyhawk'

const cronTime = require('cron-time-generator')

export class MyChart extends PennLabsChart {
	constructor(scope: Construct) {
		super(scope)

		const backendImage = 'pennlabs/penn-courses-backend'
		const secret = 'penn-courses'
		const ingressProps = {
			annotations: {
				['ingress.kubernetes.io/content-security-policy']:
					"frame-ancestors 'none';",
				['ingress.kubernetes.io/protocol']: 'https',
				['traefik.ingress.kubernetes.io/router.middlewares']:
					'default-redirect-http@kubernetescrd',
			},
		}

		new RedisApplication(this, 'redis', {
			persistData: false,
		})

		new DjangoApplication(this, 'celery', {
			deployment: {
				image: backendImage,
				secret,
				cmd: [
					'celery',
					'-A',
					'PennCourses',
					'worker',
					'-Q',
					'alerts,celery',
					'-linfo',
				],
			},
			djangoSettingsModule: 'PennCourses.settings.production',
		})

		new DjangoApplication(this, 'backend', {
			deployment: {
				image: backendImage,
				secret,
				replicas: 2,
			},
			djangoSettingsModule: 'PennCourses.settings.production',
			ingressProps,
			domains: [
				{
					host: 'penncourseplan.com',
					paths: ['/api', '/admin', '/accounts', '/assets'],
				},
				{
					host: 'penncoursealert.com',
					paths: ['/api', '/admin', '/accounts', '/assets', '/webhook'],
				},
				{
					host: 'penncoursereview.com',
					paths: ['/api', '/admin', '/accounts', '/assets'],
				},
				{
					host: 'penndegreeplan.com',
					paths: ['/api', '/admin', '/accounts', '/assets'],
				},
				{
					host: 'penncourses.org',
					paths: ['/api', '/admin', '/accounts', '/assets'],
				},
			],
		})

		new DjangoApplication(this, 'backend-asgi', {
			deployment: {
				image: backendImage,
				cmd: ['/usr/local/bin/asgi-run'],
				secret,
				replicas: 1,
			},
			djangoSettingsModule: 'PennCourses.settings.production',
			ingressProps,
			domains: [{ host: 'penncoursereview.com', paths: ['/api/ws'] }],
		})

		new ReactApplication(this, 'landing', {
			deployment: {
				image: 'pennlabs/pcx-landing',
			},
			domain: { host: 'penncourses.org', paths: ['/'] },
		})

		new ReactApplication(this, 'plan', {
			deployment: {
				image: 'pennlabs/pcp-frontend',
			},
			domain: { host: 'penncourseplan.com', paths: ['/'] },
		})

		new ReactApplication(this, 'alert', {
			deployment: {
				image: 'pennlabs/pca-frontend',
			},
			domain: { host: 'penncoursealert.com', paths: ['/'] },
		})

		new ReactApplication(this, 'review', {
			deployment: {
				image: 'pennlabs/pcr-frontend',
			},
			domain: { host: 'penncoursereview.com', paths: ['/'] },
		})

		new ReactApplication(this, 'degree', {
			deployment: {
				image: 'pennlabs/pdp-frontend',
			},
			domain: { host: 'penndegreeplan.com', paths: ['/'] },
		})

		new CronJob(this, 'load-courses', {
			schedule: cronTime.everyDayAt(3),
			image: backendImage,
			secret,
			cmd: ['python', 'manage.py', 'registrarimport'],
		})

		new CronJob(this, 'report-stats', {
			schedule: cronTime.everyDayAt(20),
			image: backendImage,
			secret,
			cmd: ['python', 'manage.py', 'alertstats', '1', '--slack'],
		})

		new CronJob(this, 'sync-path-course-statuses', {
			schedule: cronTime.every(5).minutes(),
			image: backendImage,
			secret,
			cmd: ['python', 'manage.py', 'sync_path_status', '--slack'],
		})
	}
}

const app = new App()
new MyChart(app)
app.synth()
