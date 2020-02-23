/* eslint-disable */
import React, {Component} from 'react'

export default class Block extends Component {
    render() {
        // Display a warning if the class requires another section
        let warning = <div className={"NeedAssc"}
                           title={"Registration is required for an associated section."}><b>!</b></div>;
        // The showWarning prop is passed down from the Schedule component
        if (!this.props.showWarning) {
            warning = null;
        }
        const removeSchedItem = this.props.removeSchedItem;
        return <div className={"SchedBlock_container " + this.props.letterDay + " " + this.props.topC}
                    style={{
                        left: this.props.x + "%",
                        top: this.props.y + "%",
                        width: this.props.width + "%",
                        height: this.props.height + "%"
                    }}>
            <div
                className={"SchedBlock " + this.props.letterDay + " " + this.props.topC + " " + this.props.assignedClass}
                id={this.props.id}
                onClick={() => {
                }}>
                <div className={"CloseX"} style={{width: 100 + "%", height: 100 + "%"}}><span
                    onClick={e => {
                        removeSchedItem(this.props.id);
                        e.stopPropagation();
                    }}>X</span></div>
                {warning}
                <span className={"SecName"}>{this.props.name}</span>
            </div>
        </div>
    }
}