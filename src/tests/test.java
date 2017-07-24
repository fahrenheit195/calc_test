package tests;

import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;

import static calc.form1.numCheck;
import static org.testng.AssertJUnit.assertEquals;
import static org.testng.AssertJUnit.assertFalse;

public class test {

    @DataProvider
    public Object[][] testInput(){
        return  new Object[][]{
                {true, "132"},
                {false, "abc"},
                {false, "a1a2s"},
        };
    }

    @Test(dataProvider = "testInput")
    public void test(Boolean result, String val){
        assertEquals(result, numCheck(val));
    }
}
