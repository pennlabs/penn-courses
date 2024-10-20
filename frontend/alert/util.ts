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
