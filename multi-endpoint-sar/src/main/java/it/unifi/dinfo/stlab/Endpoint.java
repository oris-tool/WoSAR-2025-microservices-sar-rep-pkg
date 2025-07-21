package it.unifi.dinfo.stlab;

public record Endpoint(String id, double arrivalRate, double serviceRate, double healthyToAgedTendency,
        double agedToFailedTendency) {

    public static String getAttributeOreder(){
        return "id,arrivalRate,serviceRate,healthyToAgedTendency,agedToFailedTendency";
    }

    @Override
    public String toString() {
        return id + "," +
                arrivalRate + "," +
                serviceRate + "," +
                healthyToAgedTendency + "," +
                agedToFailedTendency;
    }
}
