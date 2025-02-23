import ScoreBox from "@/components/ScoreBox";
import { Rating } from "@/lib/types";
import { cn } from "@/lib/utils";
export default function FAQ() {
    return (
        <div id="faqs" className={cn("mx-[10%]")}>
            <h2>Frequently Asked Questions</h2>
            <div>
                <p className="question">How do I use the website?</p>
                <p className="answer">
                    Each professor, course, and department has its own page.
                    Summary ratings for the recent semester and for all
                    semesters are provided at the left of each page, with more
                    detailed rating information provided on the right. You can
                    choose to view or hide each course rating criteria by
                    clicking the plus icon on the top of the table. You can also
                    toggle the view mode of ratings between aggregate and most
                    recent on the right side of the page. You can hover over the
                    tags on the left side of the page or the stars on the right
                    side of the page in order to learn more about courses
                    offered in the upcoming semester.
                </p>
            </div>

            <div>
                <p className="question">What&apos;s new?</p>
                <p className="answer">
                    The site includes new features intended to make PCR&apos;s
                    content more intuitive and accessible. The new search
                    function allows students to search by course name, number,
                    or professor. In addition to the traditional ratings, the
                    site now offers ratings that average the evaluations from
                    every semester the course or professor has been reviewed.
                    Students can choose which information is relevant to them by
                    selecting which rating criteria appear on the page. As of
                    fall 2021, PCR now also displays additional metrics to give
                    students a sense of registration difficulty. See the section
                    about &quot;Registration Metrics&quot; below for more
                    information.
                </p>
            </div>

            <div>
                <p className="question">How are courses rated?</p>
                <p className="answer">
                    At the end of each semester, the Provost&apos;s office, in
                    conjunction with ISC, administers Penn&apos;s course
                    evaluation form, which consists of eleven questions aimed at
                    assessing the quality of the course and instructor. Each
                    evaluation question is answered on a scale of Poor to
                    Excellent. The ratings are translated numerically so that a
                    rating of 0.00 corresponds a student evaluation of
                    &quot;Poor,&quot; 1.00 corresponds to an evaluation of
                    &quot;Fair,&quot; 2.00 to &quot;Good,&quot; 3.00 to
                    &quot;Very Good,&quot; and 4.00 to &quot;Excellent.&quot;
                </p>
            </div>

            <div>
                <p className="question">How often is data updated?</p>
                <p className="answer">
                    Information pertaining to which sections are taught in the
                    upcoming semester is updated every 24 hours.
                </p>
            </div>

            <div>
                <p className="question">What do the colors mean?</p>
                <div className="answer">
                    Here&apos;s a guide to the color coded ratings.
                    <br />
                    <br />
                    <ScoreBox rating={Rating.Bad}>0-2</ScoreBox>
                    <ScoreBox rating={Rating.Good}>2-3</ScoreBox>
                    <ScoreBox rating={Rating.Okay}>3-4</ScoreBox>
                    <br />
                    <br />
                </div>
            </div>

            <div>
                <p className="question">
                    What are &quot;Registration Metrics&quot;?
                </p>
                <p className="answer">
                    As of fall 2021, PCR now also displays additional metrics to
                    give students a sense of registration difficulty (such as
                    avg. number of course openings, avg. final enrollment, avg.
                    percentage of the semester open, percentage of sections
                    filled in advance registration, and plots of estimated
                    registration difficulty / percent of historical sections
                    open over time). Generally, these metrics can give you a
                    sense of how difficult it will be to register for a course
                    (which is important for planning out your course
                    registration). You can view these metrics by clicking the
                    &quot;Registration Metrics&quot; tab in the left window on
                    an instructor, department, or course page. For more
                    information about any specific metric, hover over the
                    question mark icon next to its name (or for plots, see the
                    description below the title).
                </p>
            </div>
        </div>
    );
}
