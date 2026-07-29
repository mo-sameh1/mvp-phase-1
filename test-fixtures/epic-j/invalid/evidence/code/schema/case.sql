create table permit_case (
    case_id varchar(40) primary key,
    applicant_id varchar(40) not null,
    status varchar(30) not null,
    submitted_at timestamp not null
);

create table case_audit_event (
    event_id varchar(40) primary key,
    case_id varchar(40) not null references permit_case(case_id),
    event_type varchar(60) not null,
    created_at timestamp not null
);
