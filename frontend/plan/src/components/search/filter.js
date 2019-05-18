import React from "react";
import connect from "react-redux/es/connect/connect";
import { OutClickable } from "../dropdown";
import { toggleSearchFilterShown } from "../../actions";

class SearchFilter extends OutClickable {
    // This has to be there for OutClickable to work
    collapse = () => (
        this.props.initiateCollapse()
    )

    render() {
        const {
            show,
            location,
        } = this.props;

        const visibility = show ? "visible" : "hidden";
        const opacity = show ? 1 : 0;
        return (
            <div
                id="FilterSearch"
                className="content_dropdown box"
                ref={this.setWrapperRef} // this function does not exist
                style={
                    location ? {
                        opacity,
                        visibility,
                        left: `${1.5 * location.left - location.right}px`,
                        top: `${location.bottom + 10}px`,
                    } : {}
                }
            >
                <div className="FilterPanel" style={{ width: "60%" }}>
                    <div className="FilterBlock">
                        <div id="reqTypes">
                            <span>College</span>
                            <span>Wharton</span>
                            <span>Engineering</span>
                        </div>
                    </div>
                </div>

                <div className="FilterPanel">
                    <div className="FilterBlock">
                        <input type="checkbox" id="closedCheck" value="ClosedSec" checked />
                        Show closed sections
                    </div>

                    <div className="FilterBlock">
                        <select id="actFilter">
                            <option value="noFilter">Filter by section type</option>
                            <option value="LEC">Lecture</option>
                            <option value="REC">Recitation</option>
                            <option value="LAB">Laboratory</option>
                            <option value="IND">Independent Study</option>
                            <option value="SEM">Seminar</option>
                            <option value="SRT">Senior Thesis</option>
                            <option value="STU">Studio</option>
                            <option value="CLN">Clinic</option>
                            <option value="PRC">SCUE Preceptorial</option>
                            <option value="PRO">NSO Proseminar</option>
                            <option value="ONL">Online Course</option>
                        </select>

                        <select id="credSelect">
                            <option value="noFilter">Filter by CU</option>
                            <option value="0.5">0.5 CU</option>
                            <option value="1">1 CU</option>
                            <option value="1.5">1.5 CU</option>
                        </select>
                    </div>

                    <div className="FilterBlock">
                        <select id="proFilter">
                            <option value="noFilter">Filter by program</option>
                            <option value="MSL">ABCS Courses</option>
                            <option value="BFS">Ben Franklin Seminars</option>
                            <option value="CGS">College of Liberal &amp; Professional Studies</option>
                            <option value="CRS">Critical Writing Seminars</option>
                            <option value="FORB">Freshman-Friendly courses</option>
                            <option value="MFS">Freshman Seminars</option>
                            <option value="PLC">Penn Language Center</option>
                            <option value="SS">Summer Sessions I &amp; II</option>
                        </select>
                    </div>
                </div>
            </div>
        );
    }
}

const mapStateToProps = state => ({
    show: state.sections.showSearchFilter,
    location: state.sections.showSearchFilterLocation,
});

const mapDispatchToProps = dispatch => ({
    initiateCollapse: () => dispatch(toggleSearchFilterShown()),
});

export default connect(mapStateToProps, mapDispatchToProps)(SearchFilter);
