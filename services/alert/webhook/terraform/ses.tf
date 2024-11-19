resource "aws_ses_template" "course_alert" {
  name    = "PennCourseAlert"
  subject = "{{courseCode}} is now open!"
  html    = file("pca.template.html")
  text    = "{{courseCode}} just opened up!"
}
