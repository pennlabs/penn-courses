export const mapActivityToString = (activity) => {
    const activityStringMap = {
        CLN: "Clinics",
        DIS: "Dissertations",
        IND: "Independent Studies",
        LAB: "Labs",
        LEC: "Lectures",
        MST: "Masters Theses",
        REC: "Recitations",
        SEM: "Seminars",
        SRT: "Senior Theses",
        STU: "Studios",
        ONL: "Online",
    };

    return activity in activityStringMap ? activityStringMap[activity] : "";
};

export function groupByProperty(
    array,
    sortingFn,
    splitPattern,
    keyExtractor,
    activityExtractor = (obj) => undefined
) {
    return array.sort(sortingFn).reduce((res, obj) => {
        const key = keyExtractor(obj);
        const activity = activityExtractor(obj);
        const [courseName, midNum, endNum] = key.split(splitPattern);
        if (activity) {
            if (res[`${courseName}-${midNum}`]) {
                if (res[`${courseName}-${midNum}`][activity]) {
                    res[`${courseName}-${midNum}`][activity].push(obj);
                } else {
                    res[`${courseName}-${midNum}`][activity] = [obj];
                }
            } else {
                res[`${courseName}-${midNum}`] = { [activity]: [obj] };
            }
        } else {
            if (res[`${courseName}-${midNum}`]) {
                res[`${courseName}-${midNum}`].push(obj);
            } else {
                res[`${courseName}-${midNum}`] = [obj];
            }
        }
        return res;
    }, {});
}
