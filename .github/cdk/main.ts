import { Construct } from "constructs";
import { App, Stack } from "cdkactions";
// import { DeployJob, DjangoProject, DockerPublishJob, ReactProject } from "@pennlabs/kraken";

export class MyStack extends Stack {
  constructor(scope: Construct, name: string) {
    super(scope, name);

    // define workflows here
    // const workflow = new Workflow(this, "workflow", {
    //   name: "Workflow",
    //   on: "push",
    // });

    // const django = new DjangoProject(workflow, {
    //   projectName: "PennCourses-degree",
    //   path: "backend",
    //   imageName: "penn-courses-backend",
    //   checkProps: {
    //     pythonVersion: "3.10-buster",
    //   }
    // });

    // const degree = new ReactProject(workflow, {
    //   id: "pdp",
    //   path: "frontend",
    //   imageName: "pdp-frontend",
    //   publishProps: {
    //     dockerfile: "degree/Dockerfile",
    //   },
    // });

    // new DeployJob(
    //   workflow,
    //   {},
    //   {
    //     needs: [
    //       django.publishJobId,
    //       degree.publishJobId,
    //     ],
    //   }
    // );
  }
}

const app = new App();
new MyStack(app, "cdk");
app.synth();
