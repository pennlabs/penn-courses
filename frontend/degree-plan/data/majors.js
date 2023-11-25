import reqs from './requirements';
import courses from "./courses";

const realmajor0 = {
    "id": 1,
    "name": "Computer Science, BSE",
    "credits": 37,
    "requirements": [
        {
            "id": 2,
            "name": "Probability",
            "num": 1,
            "satisfied_by": 2,
            "topics": courses,
            // "Topic 36424 (GPRD-9660 most recently)",
            // "Topic 36433 (HCMG-0099 most recently)",
            // "Topic 36432 (HCIN-6070 most recently)"
            "subrequirements": []
        }
    ]
}

const realmajor1 = {
    "id": 1,
    "name": "Computer Science, BSE",
    "credits": 37,
    "requirements": [
        {
            "id": 2,
            "name": "Probability",
            "num": 1,
            "satisfied_by": 2,
            "topics": courses,
            // "Topic 36424 (GPRD-9660 most recently)",
            // "Topic 36433 (HCMG-0099 most recently)",
            // "Topic 36432 (HCIN-6070 most recently)"
            "subrequirements": []
        }
    ]
}

const major1 = {
    name: "CIS",
    requirements: reqs
}


const major2 = {
    name: "MATH",
    requirements: [reqs[0]]
}

const major3 = {
    name: "LOGIC",
    requirements: [reqs[1]]
}

const major4 = {
    name: "Premed",
    requirements: [reqs[1]]
}

export default [realmajor0, realmajor1];