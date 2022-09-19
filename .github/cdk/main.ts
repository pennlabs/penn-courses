import { Construct } from "constructs";
import { App, Stack, Workflow } from "cdkactions";
import { DeployJob, DjangoProject, DockerPublishJob, ReactProject } from "@pennlabs/kraken";

export class MyStack extends Stack {
  constructor(scope: Construct, name: string) {
    super(scope, name);

    // define workflows here
    const workflow = new Workflow(this, "workflow", {
      name: "Workflow",
      on: "push",
    });

    const django = new DjangoProject(workflow, {
      projectName: "PennCourses",
      path: "backend",
      imageName: "penn-courses-backend",
      checkProps: {
        pythonVersion: "3.10-buster",
      }
    });

    // const plan = new ReactProject(workflow, {
    //   id: "pcp",
    //   path: "frontend",
    //   imageName: "pcp-frontend",
    //   publishProps: {
    //     dockerfile: "plan/Dockerfile",
    //   },
    // });

    // const alert = new ReactProject(workflow, {
    //   id: "pca",
    //   path: "frontend",
    //   imageName: "pca-frontend",
    //   publishProps: {
    //     dockerfile: "alert/Dockerfile",
    //   },
    // });

    // const review = new ReactProject(workflow, {
    //   id: "pcr",
    //   path: "frontend",
    //   imageName: "pcr-frontend",
    //   publishProps: {
    //     dockerfile: "review/Dockerfile",
    //   },
    // });

    const landing = new DockerPublishJob(workflow, 'landing', {
      imageName: 'pcx-landing',
      path: 'frontend/landing',
    });

    new DeployJob(
      workflow,
      {},
      {
        needs: [
          django.publishJobId,
          // plan.publishJobId,
          // alert.publishJobId,
          // review.publishJobId,
          landing.id,
        ],
      }
    );
  }
}

const app = new App();
new MyStack(app, "cdk");
app.synth();
