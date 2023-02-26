import reqs from './requirements';

const major1 = {
    name: "CIS",
    reqs: reqs
}

const major2 = {
    name: "MATH",
    reqs: [reqs[0]]
}

const major3 = {
    name: "LOGIC",
    reqs: [reqs[1]]
}

const major4 = {
    name: "Premed",
    reqs: [reqs[1]]
}

export default [major1, major2, major3, major4];