# MSDE Student Demographics Data Collection Guide

## Data Sources

### Primary Source: MSDE Report Card
- **URL**: https://reportcard.msde.maryland.gov/
- **Data Updated**: Annually (typically fall for previous school year)
- **Years Available**: 2018-present

### Alternative Sources:
1. **Maryland Longitudinal Data System (MLDS)**: https://mldscenter.maryland.gov/
2. **District Websites**: Each county has data dashboards
3. **MSDE Open Data Portal**: https://www.marylandpublicschools.org/about/Pages/DAAIT/index.aspx

## Data Elements to Collect

### 1. Free/Reduced Lunch (FARMS)
- **Metric**: Percentage of students eligible for free or reduced-price meals
- **Location in Report Card**: "Student Characteristics" section
- **Note**: Indicator of economic disadvantage

### 2. McKinney-Vento Homeless Students
- **Metric**: Count and percentage of homeless students
- **Location**: "Special Populations" or "Student Groups"
- **Federal Program**: McKinney-Vento Homeless Assistance Act
- **Note**: May be suppressed if <10 students for privacy

### 3. English Language Learners (ELL)
- **Metric**: Count and percentage of ELL students
- **Location**: "Student Characteristics" > "English Learners"
- **Also Called**: ESOL students, English Learners

### 4. Special Education
- **Metric**: Percentage of students with IEPs (Individualized Education Programs)
- **Location**: "Special Populations" > "Students with Disabilities"
- **Federal Law**: IDEA (Individuals with Disabilities Education Act)

### 5. Attendance & Chronic Absenteeism
- **Metrics**: 
  - Average Daily Attendance Rate
  - Chronic Absenteeism Rate (missing 10%+ of school days)
- **Location**: "Attendance" section
- **Note**: Critical indicator for Blueprint accountability

## Step-by-Step Instructions

### For Each County:

1. **Navigate to MSDE Report Card**
   ```
   https://reportcard.msde.maryland.gov/
   ```

2. **Select School Level**
   - Choose "School" from dropdown
   - Or choose "LEA" (Local Education Agency) for district-level data

3. **Search for Schools**
   - Enter school name or county name
   - County LSS numbers:
     - Kent: 13
     - Dorchester: 09
     - Caroline: 05
     - Queen Anne's: 17
     - Talbot: 20

4. **Navigate to Data Sections**
   - Click on each school
   - Find "Student Characteristics"
   - Find "Attendance"
   - Find "Special Populations"

5. **Download Data**
   - Look for "Download Data" or "Export" buttons
   - Save as CSV or Excel
   - Or manually record data in JSON template

6. **Data Privacy Notes**
   - Cells with <10 students may show "***" for privacy
   - Record these as "suppressed" in the JSON

## County-Specific Notes

### Kent County Public Schools
- Total enrollment: ~1,880
- 5 schools total
- Website: https://www.kent.k12.md.us/

### Dorchester County Public Schools  
- Website: https://www.dcpsmd.org/

### Caroline County Public Schools
- Website: https://www.carolineday.org/

### Queen Anne's County Public Schools
- Website: https://www.qacps.org/

### Talbot County Public Schools
- Website: https://www.talbotschools.org/

## Updating JSON Files

After collecting data, update the corresponding files:
```
scraped_county_data/[county]/[county]_student_demographics.json
```

Replace `null` values with actual numbers or percentages.

## Example Data Entry

```json
{
  "school_name": "Rock Hall Elementary",
  "enrollment": 250,
  "free_reduced_lunch": {
    "count": 125,
    "percentage": 50.0
  },
  "homeless_students": {
    "count": "suppressed",
    "percentage": null,
    "mckinney_vento_eligible": "suppressed"
  },
  "english_learners": {
    "count": 8,
    "percentage": 3.2
  }
}
```

## Verification

Cross-reference with:
- District annual reports
- Local newspaper coverage
- Blueprint implementation reports
- County budget documents

## Questions or Issues

If data is unavailable:
- Contact district data coordinator
- File MPIA (Maryland Public Information Act) request
- Check previous years' data
