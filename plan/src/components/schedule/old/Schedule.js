/* eslint-disable */
import React, {Component} from 'react';
import Line from './Line'
import Block from './Block'
import connect from "react-redux/es/connect/connect";
import {removeSchedItem} from "../../actions";


//possible color classes (corresponds with CSS classes)
const top_colors_recitation_save = ["red", "orange", "pink"];
const top_colors_other_save = ["blue", "aqua", "green", "sea", "indigo"];

//available color classes
let top_colors_recitation = [];
let top_colors_other = [];

//makes all recitation colors available
const reset_recitation_colors = () => {
    top_colors_recitation = top_colors_recitation_save.slice();
};

//makes all other colors available
const resetOtherColors = () => {
    top_colors_other = top_colors_other_save.slice();
};

//dictionary associating class name with color
let class_colors = {};

//makes all colors available
const resetColors = () => {
    reset_recitation_colors();
    resetOtherColors();
    class_colors = {};
};

//generates a color from a given day of the week, hour, and course name
const generate_color = (day, hour, name) => {
    let temp_color = class_colors[name];
    if (temp_color !== undefined) {
        return temp_color;
    } else {
        let chosen_list = null;
        if (parseInt(name.substring(name.length - 3, name.length)) >= 100) {
            chosen_list = top_colors_recitation;
            if (chosen_list.length === 0) {
                reset_recitation_colors();
                chosen_list = top_colors_recitation;
            }
        } else {
            chosen_list = top_colors_other;
            if (chosen_list.length === 0) {
                resetOtherColors();
                chosen_list = top_colors_other;
            }
        }
        const index = (["M", "T", "W", "H", "F"].indexOf(day) % 2 + Math.round(hour * 2)) % chosen_list.length;
        const result = chosen_list[index];
        chosen_list.splice(index, 1);
        class_colors[name] = result;
        return result;
    }
};

class Schedule extends Component {

    constructor(props) {
        super(props);
    }

    render() {
        if (!this.props.schedData) {
            return EmptySchedule();
        }
        const courseSched = this.props.schedData.meetings;
        let weekdays = ['M', 'T', 'W', 'R', 'F'];
        let fullWeekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
        let startHour = 10; // start at 10
        let endHour = 15; // end at 3pm
        let incSun = 0; // no weekends
        let incSat = 0;

        if (courseSched) {
            courseSched.forEach(function (sec) {
                var secMeetHour = sec.meetHour;
                if (secMeetHour <= startHour) {
                    // If there are classes earlier than the default start
                    startHour = Math.floor(secMeetHour); // push back the earliest hour
                }
                if (secMeetHour + sec.hourLength >= endHour) {
                    // Push back latest hour if necessary
                    endHour = Math.ceil(secMeetHour + sec.hourLength);
                }
                if (sec.meetDay === 'U') {
                    // If there are sunday classes
                    incSun = 1;
                }
                if (sec.meetDay === 'S') {
                    // If there are saturday classes
                    incSat = 1;
                }
            });
        }

        if (incSun === 1) {
            weekdays.unshift('U');
            fullWeekdays.unshift('Sunday');
        } // Update weekdays array if necessary
        if (incSat === 1) {
            weekdays.push('S');
            fullWeekdays.push('Saturday');
        }
        let percentWidth = 100 / weekdays.length; // Update the block width if necessary
        let halfScale = 95 / (endHour - startHour + 1); // This defines the scale to be used throughout the scheduling process

        let timeblocks = [];
        let lines = [];

        if (courseSched && courseSched.length) {
            for (let h = 0; h <= endHour - startHour; h++) {
                // for each hour
                let toppos = h * halfScale + 7.5; // each height value is linearly spaced with an offset
                let hourtext = Math.round(h + startHour); // If startHour is not an integer, make it pretty
                if (hourtext >= 12) {
                    if (hourtext !== 12) {
                        hourtext -= 12;
                    }
                    hourtext += "PM";
                } else {
                    hourtext += "AM";
                }
                lines.push(<Line key={h} y={toppos}/>);
                timeblocks.push(<div className="TimeBlock" style={{top:toppos+"%"}}>{hourtext}</div>);
            }
        }

        function GenMeetBlocks(sec) {
            const blocks = [];
            const meetLetterDay = sec.meetDay; // On which day does this meeting take place?
            const meetRoom = sec.meetLoc;
            const newid = sec.idDashed + '-' + meetLetterDay + sec.meetHour.toString().replace(".", "");
            const asscsecs = sec.SchedAsscSecs;

            const newblock = {
                'class': sec.idDashed,
                'letterday': meetLetterDay,
                'id': newid,
                'startHr': sec.meetHour,
                'duration': sec.hourLength,
                'name': sec.idSpaced,
                'room': meetRoom,
                'asscsecs': asscsecs,
                "topc": "blue",
                'showWarning': asscsecs.filter(value => -1 !==
                    courseSched.map((course) => course.idDashed).indexOf(value)).length === 0
            };
            blocks.push(newblock);
            return blocks;
        }

        var meetBlocks = [];
        let schedBlocks = [];
        // Add the blocks
        if (courseSched) {
            courseSched.forEach(function (sec) {
                meetBlocks = meetBlocks.concat(GenMeetBlocks(sec));
            });
        }

        function AddSchedAttr(block) {
            block.left = weekdays.indexOf(block.letterday) * percentWidth;
            block.top = (block.startHr - startHour) * halfScale + 9; // determine top spacing based on time from startHour (offset for prettiness)
            block.height = block.duration * halfScale;
            block.width = percentWidth;
            block.topc = generate_color(block.letterday, block.startHr, block.name);
            return block;
        }

        resetColors();

        meetBlocks.forEach(function (b) {
            schedBlocks.push(b);
        });

        /**
         * @return {boolean}
         */
        function TwoOverlap(block1, block2) {
            // Thank you to Stack Overflow user BC. for the function this is based on.
            // http://stackoverflow.com/questions/5419134/how-to-detect-if-two-divs-touch-with-jquery
            var y1 = (block1.startHr || block1.top);
            var h1 = (block1.duration || block1.height);
            var b1 = y1 + h1;

            var y2 = (block2.startHr || block2.top);
            var h2 = (block2.duration || block2.height);
            var b2 = y2 + h2;

            // This checks if the top of block 2 is lower down (higher value) than the bottom of block 1...
            // or if the top of block 1 is lower down (higher value) than the bottom of block 2.
            // In this case, they are not overlapping, so return false
            return !(b1 <= (y2 + 0.0000001) || b2 <= (y1 + 0.0000001));
        }

        let newSchedBlocks = [];
        weekdays.forEach(function (weekday) {
            let dayblocks = [];
            schedBlocks.forEach(function (n) {
                if (n.letterday.indexOf(weekday) !== -1) {
                    let newObj = JSON.parse(JSON.stringify(n));
                    newObj.letterday = weekday;
                    newObj.showWarning = n.showWarning;
                    dayblocks.push(AddSchedAttr(newObj));
                }
            });
            for (var i = 0; i < dayblocks.length - 1; i++) {
                for (var j = i + 1; j < dayblocks.length; j++) {
                    if (TwoOverlap(dayblocks[i], dayblocks[j])) {
                        dayblocks[i].width = dayblocks[i].width / 2;
                        dayblocks[j].width = dayblocks[j].width / 2;
                        dayblocks[j].left = dayblocks[j].left + dayblocks[i].width;
                    }
                }
            }
            newSchedBlocks = newSchedBlocks.concat(dayblocks);
        });

        schedBlocks = newSchedBlocks;

        let blocks = [];
        for (let i = 0; i < schedBlocks.length; i++) {
            const block = schedBlocks[i];
            // TODO: Check for associated section
            blocks.push(<Block topC={block.topc} id={block.id}
                               assignedClass={block.class} letterDay={block.letterday}
                               key={i} y={block.top} x={block.left} width={block.width}
                               height={block.height} name={block.name}
                               showWarning={block.showWarning}
                               removeSchedItem={this.props.removeSchedItem}/>);
        }
        if (blocks.length === 0) {
            return <EmptySchedule/>
        } else {
            let weekdays = [];
            const weekdayNames = fullWeekdays;
            for (let i = 0; i < weekdayNames.length; i++) {
                var weekday = weekdayNames[i];
                let label = <div key={i} className="DayName"
                                 style={{width: percentWidth + "%"}}>
                    {weekday}
                </div>;
                weekdays.push(label);
            }
            return <div id={"SchedGraph"} className={"box"}>
                <div id={"TimeCol"} style={{position:"relative"}}>
                    {timeblocks}
                </div>
                <div id="Schedule" style={{position: 'relative'}}>
                    {weekdays}
                    <div id={"SchedGrid"}>
                        {lines}{blocks}
                    </div>
                </div>
            </div>;
        }
    }
}

const mapStateToProps = (state) => {
    return {
        schedData: state.schedule.schedules[state.schedule.scheduleSelected]
    };
};

const mapDispatchToProps = (dispatch) => (
    {
        removeSchedItem: idDashed => dispatch(removeSchedItem(idDashed))
    }
);

export default connect(mapStateToProps, mapDispatchToProps)(Schedule);

const EmptySchedule = () => (
    <div>
        <p style={{fontSize: "1.5em", marginTop: "7em", display: "block"}}>
            Search for courses above <br/>then click a section's + icon to add it to the schedule.
        </p>
        <p style={{fontSize: "1em"}}>
            These are mock schedules.
            <br/>
            You still need to register for your classes on Penn InTouch.
        </p>
    </div>
);